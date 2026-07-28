"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import inspect
import json
import os
import re
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()
FALLBACK_MESSAGE = (
    "Xin lỗi, tôi chưa thể hoàn tất yêu cầu này sau nhiều lần thử. "
    "Bạn vui lòng cung cấp lại thông tin (triệu chứng/khoa/ngày) rõ ràng hơn "
    "hoặc liên hệ trực tiếp lễ tân để được hỗ trợ."
)

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider) -> str:
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response

# ---------------------------------------------------------------------------
# ReAct Agent Loop — parser + executor + guardrails (Agent V2)
# ---------------------------------------------------------------------------

def _parse_args(raw: str):
    """Tách chuỗi tham số 'a, b, c' thành list, bỏ dấu nháy nếu có."""
    raw = raw.strip()
    if not raw:
        return []
    args = []
    for part in raw.split(","):
        part = part.strip()
        if len(part) >= 2 and part[0] == part[-1] and part[0] in ("'", '"'):
            part = part[1:-1]
        args.append(part)
    return args


def parse_llm_step(response: str) -> dict:
    """
    Phân tích 1 phản hồi LLM thành đúng 1 bước ReAct (Thought + Action, hoặc Thought + Final Answer).
    Cắt bỏ mọi nội dung sau 'Observation:' vì LLM không được phép tự bịa Observation.
    """
    text = response.strip()
    obs_idx = text.find("Observation:")
    if obs_idx != -1:
        text = text[:obs_idx].strip()

    thought_match = re.search(r"Thought:\s*(.*?)(?:\n(?:Action|Final Answer):|\Z)", text, re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else ""

    fa_idx = text.find("Final Answer:")
    action_idx = text.find("Action:")

    if fa_idx != -1 and (action_idx == -1 or fa_idx < action_idx):
        answer = text[fa_idx + len("Final Answer:"):].strip()
        # Phòng trường hợp model bịa thêm bước Thought/Action tiếp theo sau Final Answer
        answer = re.split(r"\n(?:Thought|Action):", answer)[0].strip()
        return {"type": "final", "thought": thought, "answer": answer}

    action_match = re.search(r"Action:\s*(\w+)\s*\[(.*?)\]", text, re.DOTALL)
    if action_match:
        tool_name = action_match.group(1).strip()
        args = _parse_args(action_match.group(2))
        return {"type": "action", "thought": thought, "tool": tool_name, "args": args}

    return {"type": "malformed", "thought": thought, "raw": text}


def execute_tool(tool_name: str, args: list) -> str:
    """Thực thi tool theo tên, kèm xử lý lỗi Unknown Tool / Malformed Args / Crash (Agent V2)."""
    if tool_name not in AVAILABLE_TOOLS:
        valid = ", ".join(AVAILABLE_TOOLS.keys())
        return f"LỖI: Tool '{tool_name}' không tồn tại. Các tool hợp lệ gồm: [{valid}]."

    func = AVAILABLE_TOOLS[tool_name]
    expected_params = list(inspect.signature(func).parameters.keys())
    if len(args) != len(expected_params):
        return (
            f"LỖI: Tool '{tool_name}' cần {len(expected_params)} tham số ({', '.join(expected_params)}) "
            f"nhưng nhận {len(args)}. Cú pháp đúng: {tool_name}[{', '.join(expected_params)}]."
        )

    try:
        return func(*args)
    except Exception as e:
        return f"LỖI hệ thống khi gọi tool '{tool_name}': {e}"


def run_react_agent(user_query: str, provider) -> dict:
    """
    Vòng lặp ReAct Agent V2 (Thought -> Action -> Observation) với:
    - Parser thật đọc phản hồi LLM (không hardcode kịch bản).
    - Executor gọi tool thật qua AVAILABLE_TOOLS.
    - Guardrail MAX_ITERATIONS chống lặp vô hạn.
    - Phát hiện Repeated Action & Unknown Tool / Malformed Args để tự phục hồi (recovery).
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    scratchpad = f"Question: {user_query}\n"
    last_action_signature = None

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        response = provider.generate(scratchpad, system_prompt=REACT_SYSTEM_PROMPT)
        parsed = parse_llm_step(response)

        if parsed["thought"]:
            print(f"🧠 Thought: {parsed['thought']}")

        if parsed["type"] == "final":
            print(f"🏁 Final Answer: {parsed['answer']}")
            scratchpad += f"Thought: {parsed['thought']}\nFinal Answer: {parsed['answer']}\n"
            return {"status": "success", "answer": parsed["answer"], "steps": step, "trace": scratchpad}

        if parsed["type"] == "action":
            args_repr = ", ".join(parsed["args"])
            action_signature = f"{parsed['tool']}[{args_repr}]"
            print(f"🛠️ Action: {action_signature}")

            if action_signature == last_action_signature:
                obs = (
                    f"LỖI: Bạn vừa lặp lại đúng hành động '{action_signature}' đã thực hiện ở bước trước. "
                    "Hãy đổi tham số hoặc dừng lại và xin lỗi người dùng nếu không thể tiếp tục."
                )
            else:
                obs = execute_tool(parsed["tool"], parsed["args"])
            last_action_signature = action_signature

            print(f"👁️ Observation: {obs}")
            scratchpad += f"Thought: {parsed['thought']}\nAction: {action_signature}\nObservation: {obs}\n"
            continue

        # Malformed: LLM không tuân theo định dạng Thought/Action/Final Answer
        obs = (
            "LỖI: Định dạng phản hồi không đúng quy tắc. Bắt buộc dùng đúng 1 trong 2 định dạng: "
            "'Thought: ...\\nAction: ten_tool[tham_so]' hoặc 'Thought: ...\\nFinal Answer: ...'."
        )
        print(f"⚠️ Parse Error: phản hồi không đúng định dạng ReAct.")
        print(f"👁️ Observation: {obs}")
        scratchpad += f"{parsed['raw']}\nObservation: {obs}\n"

    print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")
    print(f"🏁 Safe Fallback: {FALLBACK_MESSAGE}")
    return {"status": "guardrail", "answer": FALLBACK_MESSAGE, "steps": MAX_ITERATIONS, "trace": scratchpad}


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")

    for case in tests:
        print("\n" + "=" * 70)
        print(f"📋 TEST CASE #{case['id']} [{case['category']}]")
        print(f"❓ {case['question']}")
        print("=" * 70)

        print("\n--- CHẠY TRÊN CHATBOT BASELINE ---")
        run_baseline_chatbot(case["question"], provider)

        print("\n--- CHẠY TRÊN REACT AGENT ---")
        run_react_agent(case["question"], provider)
        