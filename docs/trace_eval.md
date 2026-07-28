# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Chủ đề: Trợ lý Đặt lịch khám bệnh & Tư vấn chuyên khoa*
*Provider dùng để chạy thực nghiệm: OpenAI (`gpt-4o-mini`) qua `src/providers.py`*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `4/5` | Cần suy luận 2 bước: từ triệu chứng → khoa phù hợp → đặt lịch với đúng tên khoa/ngày. |
| 🛠️ **Tool Interaction** | `5/5` | Bắt buộc tra cứu dữ liệu khoa/lịch trống thời gian thực từ hệ thống (`find_department`, `book_appointment`), không thể trả lời chính xác chỉ bằng kiến thức tĩnh. |
| 🔀 **Dynamic Decision** | `4/5` | Kết quả `find_department` (tên khoa chính xác) quyết định tham số truyền vào `book_appointment`; nếu sai lệch tên khoa sẽ dẫn tới lỗi dây chuyền. |
| ⏳ **Long Horizon** | `3/5` | Quy trình gồm 2 bước gọi tool nối tiếp, chưa phải bài toán dài hạn nhiều phiên. |
| **TỔNG ĐIỂM FIT** | **16/20** | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT** — vì cần dữ liệu khoa/lịch trống thực tế và có phụ thuộc thứ tự giữa 2 tool call. |

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3 — Multi-step, 1 Tool)

**Câu hỏi**: *"Tôi bị đau răng mấy hôm nay, tôi nên khám khoa nào và còn giờ trống không?"*

### 🤖 Chatbot Baseline:
* **Phản hồi**: *"Tôi không có quyền truy cập vào hệ thống đặt lịch hay dữ liệu về giờ khám của phòng khám, nên không thể cung cấp thông tin về thời gian trống"*
* **Nhận xét**: **không thể** trả lời phần giờ trống — đúng như kỳ vọng của baseline, thành thật về giới hạn thay vì bịa số liệu (safe fallback), 0 tool call.

### 🧠 ReAct Agent:
```
Thought: Tôi cần tìm hiểu khoa khám phù hợp với triệu chứng đau răng của bạn.
Action: find_department[đau răng]
Observation: Triệu chứng 'đau răng' phù hợp với Khoa Răng Hàm Mặt. Khung giờ còn trống hôm nay: 08:30, 10:00, 15:30.

Thought: Tôi đã biết khoa phù hợp và giờ khám còn trống hôm nay.
Final Answer: Bạn nên đến Khoa Răng Hàm Mặt để khám. Hôm nay, khoa có các giờ khám còn trống là 08:30, 10:00 và 15:30. Vui lòng cho tôi biết tên của bạn và bạn muốn đặt lịch khám vào giờ nào.
```
* **Nhận xét**: Có **Observation thật** làm bằng chứng cho tên khoa lẫn khung giờ trống — Chatbot chỉ đoán được vế đầu, Agent trả lời đầy đủ và có grounding.

---

## 🧯 3. FAILED TRACE → ROOT CAUSE ANALYSIS (TEST CASE #4)

**Câu hỏi**: *"Tôi tên Nguyễn Văn A, bị đau bụng dữ dội. Hãy tìm khoa phù hợp và đặt lịch khám cho tôi vào ngày 30/07/2026."*

### Trace log thật (Agent V1 — chưa có Repeated Action Guard):
```
Step 1
Thought: Tôi cần tìm khoa khám phù hợp với triệu chứng đau bụng dữ dội của bệnh nhân Nguyễn Văn A trước.
Action: find_department[đau bụng dữ dội]
Observation: Triệu chứng 'đau bụng dữ dội' phù hợp với Khoa Tiêu Hóa. Khung giờ còn trống hôm nay: 07:30, 09:00, 13:30.

Step 2
Thought: Tôi đã xác định được khoa phù hợp là Khoa Tiêu Hóa. Bây giờ tôi sẽ tiến hành đặt lịch khám.
Action: book_appointment[Tiêu Hóa, 30/07/2026, Nguyễn Văn A]
Observation: LỖI: Khoa 'Tiêu Hóa' không tồn tại trong hệ thống. Các khoa hợp lệ: Khoa Nội Thần Kinh, Khoa Răng Hàm Mặt, Khoa Tiêu Hóa, Khoa Hô Hấp, Khoa Tim Mạch, Khoa Cơ Xương Khớp, Khoa Nội Tổng Quát.

Step 3
Thought: Có vẻ như tôi đã sử dụng tên khoa không chính xác. Tôi cần xác nhận lại tên khoa đúng và thử lại.
Action: book_appointment[Tiêu Hóa, 30/07/2026, Nguyễn Văn A]   ⚠️ GỌI LẠI Y HỆT LẦN TRƯỚC
```

### 🔎 Root Cause Analysis (RCA):
| Mục | Phân tích |
| :--- | :--- |
| **Dạng lỗi** | *Malformed Args* (thiếu tiền tố `"Khoa "`) dẫn tới *Repeated Action* — LLM tự nhận ra sai nhưng vẫn lặp lại y hệt tham số cũ ở bước kế. |
| **Nguyên nhân gốc** | 1) Observation của `find_department` chỉ nêu `"phù hợp với Khoa Tiêu Hóa"` trong câu văn, LLM trích ra `"Tiêu Hóa"` thay vì cả cụm `"Khoa Tiêu Hóa"`. 2) `book_appointment` so khớp tên khoa **chính xác tuyệt đối** (exact match) với `DEPARTMENT_SLOTS`, không có fuzzy matching hay gợi ý sửa lỗi trong thông báo lỗi đủ rõ để LLM tự literal-copy. |
| **Vì sao Agent V1 dễ kẹt** | Không có cơ chế phát hiện "đây là hành động y hệt bước trước" ⇒ nếu LLM tiếp tục đoán sai theo cùng 1 kiểu, vòng lặp chỉ dừng khi chạm `MAX_ITERATIONS`, tốn budget mà không tạo thêm giá trị. |

### ✅ Khắc phục ở Agent V2 (`src/app.py::run_react_agent`):
1. **Repeated Action Guard**: so sánh `action_signature` (tool + args) của bước hiện tại với bước liền trước; nếu trùng, **không gọi lại tool** mà trả Observation đặc biệt ép LLM đổi cách tiếp cận thay vì lặp vô ích.
2. **Unknown Tool Guard**: nếu LLM gọi tool không có trong `AVAILABLE_TOOLS`, trả về danh sách tool hợp lệ để LLM tự sửa tên.
3. **Malformed Args Guard**: nếu số lượng tham số không khớp chữ ký hàm, trả về cú pháp đúng kèm tên tham số.
4. **Guardrail cứng `MAX_ITERATIONS = 4`**: nếu sau 4 bước vẫn chưa có Final Answer, Agent tự ngắt và trả lời fallback lịch sự thay vì crash hoặc treo.

### Kết quả sau khi bật Repeated Action Guard (trace thật — Agent V2):
```
Step 3
Action: book_appointment[Tiêu Hóa, 30/07/2026, Nguyễn Văn A]
Observation: LỖI: Bạn vừa lặp lại đúng hành động 'book_appointment[Tiêu Hóa, 30/07/2026, Nguyễn Văn A]' đã thực hiện ở bước trước. Hãy đổi tham số hoặc dừng lại và xin lỗi người dùng nếu không thể tiếp tục.

Step 4
Thought: Tôi đã thực hiện hai lần lệnh đặt lịch nhưng không thành công do không xác định được khoa hợp lệ với tên đúng.
Final Answer: Xin lỗi anh Nguyễn Văn A, nhưng tôi không thể đặt lịch khám cho anh vào khoa Tiêu Hóa do một số vấn đề về thông tin. Xin hãy kiểm tra lại tên khoa hoặc cung cấp thông tin khác để tôi có thể hỗ trợ tốt hơn.
```
**Before/After**: Agent V1 (không guard) sẽ tốn hết 4/4 bước gọi lặp lại tool sai tham số 2-3 lần rồi mới chạm Guardrail cứng. Agent V2 phát hiện lặp lại ngay ở bước 3, buộc dừng và trả lời Safe Fallback sớm hơn — tiết kiệm 1 lượt gọi LLM/tool, không giả vờ đã đặt lịch thành công (không hallucinate kết quả).

> ⚠️ **Hạn chế còn tồn đọng**: Agent chưa tự sửa `"Tiêu Hóa"` → `"Khoa Tiêu Hóa"` dù dữ liệu đã có trong Observation trước đó. Cải tiến V3 tiềm năng: chuẩn hoá `book_appointment` chấp nhận tên khoa không cần tiền tố `"Khoa "` (so khớp linh hoạt hơn), hoặc yêu cầu `find_department` trả về tên khoa dạng field riêng thay vì lồng trong câu văn.

---

## 📋 4. BẢNG TỔNG HỢP 5 TEST CASES (Chatbot vs Agent)

| # | Loại | Chatbot Baseline | ReAct Agent | Rubric (0–2đ mỗi tiêu chí) |
| :---: | :--- | :--- | :--- | :--- |
| 1 | 🟢 Đơn giản | Trả lời chung chung, không bịa số liệu cụ thể — *safe fallback hợp lý* | Cố gắng gọi `find_department` với câu hỏi không phải triệu chứng ⇒ lỗi 2 lần, cuối cùng Final Answer xin thêm thông tin (đúng hướng, tốn thêm bước không cần thiết) | Factual: 2/2 · Grounding: N/A · Tool selection: 1/2 (gọi tool không phù hợp ngữ cảnh) · Termination: 2/2 |
| 2 | 🟢 Đơn giản | Trả lời đầy đủ, đúng kiến thức phổ thông | 1 bước bị Parse Error (LLM quên định dạng `Action:`), tự phục hồi ở bước 2 và trả lời fallback lịch sự | Factual: 2/2 · Termination: 2/2 · nhưng tốn thêm 1 bước LLM call không cần thiết so với Chatbot |
| 3 | 🟡 Multi-step (1 tool) | Đoán đúng tên khoa nhưng thật thà từ chối phần giờ trống | Gọi đúng `find_department`, trả lời đầy đủ có Observation làm bằng chứng | Factual: 2/2 · Grounding: 2/2 · Tool selection: 2/2 · Termination: 2/2 |
| 4 | 🟡 Multi-step (2 tools) | Từ chối lịch sự, không bịa | Gọi đúng `find_department`, nhưng gọi `book_appointment` sai định dạng tên khoa 2 lần liên tiếp → Repeated Action Guard chặn → Final Answer xin lỗi (không hallucinate thành công) | Factual: 1/2 (không hoàn thành đặt lịch) · Grounding: 2/2 · Tool selection: 1/2 · Termination: 2/2 (dừng an toàn, không lặp vô hạn) |
| 5 | 🔴 Edge Case | Từ chối đúng, chỉ ra ngày không hợp lệ | Nhận ra ngày sai ngay ở Thought và trả Final Answer luôn **không gọi tool để xác nhận** — vi phạm nhẹ nguyên tắc "không kết luận khi thiếu Observation", nhưng kết luận vẫn đúng | Factual: 2/2 · Grounding: 1/2 (thiếu Observation làm bằng chứng) · Termination: 2/2 |

**Nhận xét tổng quát**: Ở 2 câu hỏi lý thuyết đơn giản (#1, #2), Chatbot Baseline **nhanh và rẻ hơn** (1 LLM call so với 2-3 lần của Agent) và chất lượng câu trả lời tương đương hoặc tốt hơn — đúng với cảnh báo *"đừng vội kết luận Agent luôn thắng"* trong CODELAB. Ở câu multi-step cần dữ liệu thật (#3, #4), Agent grounded và đáng tin hơn hẳn dù chi phí orchestration cao hơn. Ở Edge Case (#5), cả hai hệ thống đều tránh được hallucination, nhưng Agent lẽ ra nên gọi tool để có Observation làm bằng chứng thay vì tự suy luận ngày sai — điểm cần siết chặt hơn ở prompt V3.

---

## 🔀 5. HYBRID DECISION — KHI NÀO DÙNG CHATBOT, KHI NÀO DÙNG AGENT

Xem sơ đồ chi tiết tại [`docs/hybrid_flowchart.mermaid`](./hybrid_flowchart.mermaid).

* **Đi đường Chatbot path** khi: câu hỏi lý thuyết/quy định chung, không cần số liệu thời gian thực (Test Case #1, #2).
* **Đi đường ReAct Agent path** khi: câu hỏi cần tra cứu khoa/lịch trống thật hoặc thực hiện đặt lịch (Test Case #3, #4, #5).