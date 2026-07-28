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

# 🤖 PHẢN HỒI CHATBOT BASELINE (5 TEST CASES)

---

## 🟢 TEST CASE #1 — Câu hỏi kiến thức

**Câu hỏi**: *"Tôi nên khám sức khỏe định kỳ bao lâu một lần?"*

### 🤖 Chatbot Baseline

* **Phản hồi**: *"...không có một con số cố định áp dụng cho tất cả mọi người... người trẻ khỏe mạnh nên khám 1–3 năm/lần, người trên 40 tuổi hoặc có yếu tố nguy cơ nên khám mỗi năm một lần... tôi không có quyền truy cập vào hệ thống đặt lịch của phòng khám..."*

* **Nhận xét**: Chatbot trả lời hoàn toàn bằng kiến thức y khoa phổ thông, không cần dữ liệu thời gian thực. Đồng thời chủ động nhắc rằng mình không thể tra cứu hay đặt lịch khám. **Không có hallucination**, không bịa lịch khám hoặc thông tin hệ thống.

---

## 🟢 TEST CASE #2 — Câu hỏi kiến thức

**Câu hỏi**: *"Bệnh cảm cúm có lây không?"*

### 🤖 Chatbot Baseline

* **Phản hồi**: *"...bệnh cảm cúm là bệnh truyền nhiễm rất dễ lây lan qua giọt bắn hô hấp, tiếp xúc trực tiếp và bề mặt nhiễm virus..."*

* **Nhận xét**: Chatbot trả lời đúng kiến thức y khoa phổ thông, không cần truy cập hệ thống hay sử dụng dữ liệu của phòng khám. **Không có hallucination**, câu trả lời phù hợp với phạm vi của chatbot thông thường.

---

## 🟡 TEST CASE #3 — Multi-step (Cần Tool)

**Câu hỏi**: *"Tôi bị đau răng mấy hôm nay, tôi nên khám khoa nào và còn giờ trống không?"*

### 🤖 Chatbot Baseline

* **Phản hồi**: *"...bạn nên khám chuyên khoa Răng Hàm Mặt (hoặc Nha khoa)... tôi không có quyền truy cập vào hệ thống đặt lịch khám hay thông tin lịch trống thực tế của phòng khám nên không thể kiểm tra giờ khám..."*

* **Nhận xét**: Chatbot **đoán đúng khoa khám** nhờ kiến thức y khoa tổng quát, nhưng **không biết thông tin giờ khám thực tế** và thành thật từ chối thay vì tự bịa dữ liệu. Đây là **safe fallback**, không xảy ra hallucination về dữ liệu thời gian thực.

---

## 🟡 TEST CASE #4 — Multi-step (Cần 2 Tools)

**Câu hỏi**: *"Tôi tên Nguyễn Văn A, bị đau bụng dữ dội. Hãy tìm khoa phù hợp và đặt lịch khám cho tôi vào ngày 30/07/2026."*

### 🤖 Chatbot Baseline

* **Phản hồi**: *"...đối với đau bụng dữ dội, ban đầu có thể khám tại khoa Cấp cứu hoặc Nội Tổng quát, sau đó chuyển sang chuyên khoa Tiêu hóa nếu cần... tôi không có quyền truy cập vào hệ thống đặt lịch nên không thể đặt lịch hay cung cấp mã lịch hẹn..."*

* **Nhận xét**: Chatbot đưa ra **khuyến nghị dựa trên kiến thức y khoa**, nhưng **không biết khoa phù hợp của hệ thống phòng khám cũng như không thể đặt lịch thực tế**. Chatbot không tự tạo lịch hẹn, không bịa mã đặt lịch hay giờ khám nên **không hallucinate dữ liệu hệ thống**, chỉ dừng ở mức tư vấn chung.

---

## 🔴 TEST CASE #5 — Edge Case

**Câu hỏi**: *"Tôi muốn đặt lịch khám vào ngày 32/07/2026."*

### 🤖 Chatbot Baseline

* **Phản hồi**: *"...tháng 7 chỉ có tối đa 31 ngày nên ngày 32/07/2026 không hợp lệ... tôi không có quyền truy cập vào hệ thống đặt lịch nên không thể đặt lịch giúp bạn..."*

* **Nhận xét**: Chatbot phát hiện đúng ngày không hợp lệ và từ chối đặt lịch. Đồng thời tiếp tục khẳng định mình không có quyền truy cập hệ thống. **Không có hallucination**, không cố gắng tạo lịch hẹn hoặc xác nhận đặt lịch thành công.

---

## 📌 Nhận xét tổng quát

Qua cả 5 test case, Chatbot Baseline **không xuất hiện hiện tượng hallucination về dữ liệu thời gian thực**. Khi gặp các yêu cầu cần tra cứu lịch khám hoặc đặt lịch, chatbot luôn thừa nhận giới hạn của mình và từ chối cung cấp thông tin mà nó không thể xác minh. Tuy nhiên, chatbot vẫn **suy luận bằng kiến thức y khoa tổng quát** (ví dụ gợi ý khám Răng Hàm Mặt hoặc Nội Tổng quát), nên các câu trả lời này **không có grounding từ hệ thống phòng khám**. Điều này cho thấy Chatbot phù hợp với các câu hỏi kiến thức, nhưng không thể hoàn thành các tác vụ cần dữ liệu thực tế hoặc thao tác trên hệ thống, là điểm mà ReAct Agent có ưu thế hơn.

# 🔄 THOUGHT → ACTION → OBSERVATION TRACE

*Trích xuất từ các trace chạy ReAct Agent.*

---

## 🟢 TEST CASE #1

**Câu hỏi:** *"Tôi nên khám sức khỏe định kỳ bao lâu một lần?"*

```
Thought:
Người dùng đang hỏi về tần suất khám sức khỏe định kỳ.
Các công cụ hiện có chỉ hỗ trợ tìm khoa khám theo triệu chứng và đặt lịch khám.
Câu hỏi này không yêu cầu sử dụng tool, vì vậy tôi sẽ trả lời dựa trên kiến thức chung.

Final Answer:
Trả lời về tần suất khám sức khỏe định kỳ và giới hạn chức năng của agent.
```

**Nhận xét:** Không có Action và Observation vì không cần truy cập dữ liệu thời gian thực.

---

## 🟢 TEST CASE #2

**Câu hỏi:** *"Bệnh cảm cúm có lây không?"*

```
Thought:
Người dùng hỏi về thông tin bệnh cảm cúm.
Các tool hiện có không hỗ trợ trả lời kiến thức y khoa.
Tôi sẽ trả lời bằng kiến thức phổ thông.

Final Answer:
Vâng, cảm cúm là bệnh lây nhiễm...
```

**Nhận xét:** Không gọi tool vì đây là câu hỏi kiến thức. 

---

## 🟡 TEST CASE #3

**Câu hỏi:** *"Tôi bị đau răng mấy hôm nay, tôi nên khám khoa nào và còn giờ trống không?"*

```
Step 1

Thought:
Người dùng đang hỏi về khoa khám bệnh dựa trên triệu chứng đau răng.
Tôi cần sử dụng công cụ find_department để tra cứu khoa phù hợp.

Action:
find_department[đau răng]

Observation:
Triệu chứng 'đau răng' phù hợp với Khoa Răng Hàm Mặt.
Khung giờ còn trống hôm nay:
08:30
10:00
15:30
```

```
Step 2

Thought:
Tôi đã biết khoa khám và các khung giờ trống.
Tôi sẽ thông báo kết quả và hỏi thêm tên bệnh nhân để đặt lịch.

Final Answer:
Bạn nên khám Khoa Răng Hàm Mặt...
```

---

## 🟡 TEST CASE #4

**Câu hỏi:** *"Tôi tên Nguyễn Văn A, bị đau bụng dữ dội. Hãy tìm khoa phù hợp và đặt lịch khám cho tôi vào ngày 30/07/2026."*

```
Step 1

Thought:
Tôi cần tìm khoa khám phù hợp với triệu chứng đau bụng dữ dội.

Action:
find_department[đau bụng dữ dội]

Observation:
Triệu chứng 'đau bụng dữ dội'
→ Khoa Tiêu Hóa

Giờ trống:
07:30
09:00
13:30
```

```
Step 2

Thought:
Đã biết khoa phù hợp.
Tiếp tục đặt lịch khám.

Action:
book_appointment[Khoa Tiêu Hóa, 30/07/2026, Nguyễn Văn A]

Observation:
Đặt lịch thành công.
Mã lịch hẹn:
APT-3126
```

```
Step 3

Thought:
Đã có đầy đủ thông tin.

Final Answer:
Thông báo đặt lịch thành công cho người dùng.
```
---

## 🔴 TEST CASE #5

**Câu hỏi:** *"Tôi muốn đặt lịch khám vào ngày 32/07/2026."*

```
Thought:
Ngày 32/07/2026 không hợp lệ.
Đồng thời chưa biết triệu chứng hoặc khoa khám.
Yêu cầu người dùng nhập lại thông tin.

Final Answer:
Xin vui lòng cung cấp lại ngày hợp lệ...
```

**Nhận xét:** Agent kết thúc ngay sau bước suy luận, không gọi tool vì đầu vào không hợp lệ. 