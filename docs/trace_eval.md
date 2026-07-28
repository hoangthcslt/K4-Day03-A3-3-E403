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
