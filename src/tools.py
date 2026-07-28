"""
🛠️ TOOL REGISTRY & SCHEMAS
Chủ đề: Đặt lịch khám bệnh & tư vấn chuyên khoa.
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

import re

# Bảng tra cứu triệu chứng -> khoa phù hợp
SYMPTOM_TO_DEPARTMENT = {
    "đau đầu": "Khoa Nội Thần Kinh",
    "chóng mặt": "Khoa Nội Thần Kinh",
    "đau răng": "Khoa Răng Hàm Mặt",
    "sâu răng": "Khoa Răng Hàm Mặt",
    "đau bụng": "Khoa Tiêu Hóa",
    "đau dạ dày": "Khoa Tiêu Hóa",
    "ho": "Khoa Hô Hấp",
    "khó thở": "Khoa Hô Hấp",
    "đau ngực": "Khoa Tim Mạch",
    "tim đập nhanh": "Khoa Tim Mạch",
    "đau khớp": "Khoa Cơ Xương Khớp",
    "sốt": "Khoa Nội Tổng Quát",
}

# Bảng lịch trống theo khoa (ngày -> giờ khám còn trống)
DEPARTMENT_SLOTS = {
    "Khoa Nội Thần Kinh": ["08:00", "09:30", "14:00"],
    "Khoa Răng Hàm Mặt": ["08:30", "10:00", "15:30"],
    "Khoa Tiêu Hóa": ["07:30", "09:00", "13:30"],
    "Khoa Hô Hấp": ["08:00", "10:30", "14:30"],
    "Khoa Tim Mạch": ["09:00", "11:00", "15:00"],
    "Khoa Cơ Xương Khớp": ["08:00", "10:00", "13:00"],
    "Khoa Nội Tổng Quát": ["07:00", "09:30", "16:00"],
}

_DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")

# Theo dõi các slot đã bị đặt: {(department, date): {slot_da_dat, ...}}
# Seed sẵn một vài lịch demo đã có người đặt trước, để minh họa tình huống gần hết chỗ / hết chỗ
# khi test book_appointment (ví dụ Khoa Tiêu Hóa ngày 30/07/2026 chỉ còn đúng 1 slot trống: 13:30).
BOOKED_SLOTS: dict[tuple[str, str], set[str]] = {
    ("Khoa Tiêu Hóa", "30/07/2026"): {"07:30", "09:00"},
    ("Khoa Răng Hàm Mặt", "30/07/2026"): {"08:30"},
}


def find_department(symptom: str) -> str:
    """
    Tra cứu khoa khám phù hợp dựa trên triệu chứng của bệnh nhân.

    Args:
        symptom (str): Mô tả triệu chứng (Ví dụ: 'đau đầu', 'đau răng', 'ho')

    Returns:
        str: Tên khoa phù hợp kèm khung giờ còn trống, hoặc thông báo lỗi
             nếu không nhận diện được triệu chứng.
    """
    symptom_lower = symptom.lower().strip()
    for keyword, department in SYMPTOM_TO_DEPARTMENT.items():
        if keyword in symptom_lower:
            slots = DEPARTMENT_SLOTS.get(department, [])
            return f"Triệu chứng '{symptom}' phù hợp với {department}. Khung giờ còn trống hôm nay: {', '.join(slots)}."
    return f"LỖI: Không nhận diện được triệu chứng '{symptom}' để gợi ý khoa khám phù hợp."


def book_appointment(department: str, date: str, patient_name: str) -> str:
    """
    Đặt lịch khám cho bệnh nhân tại một khoa cụ thể.

    Args:
        department (str): Tên khoa khám (Ví dụ: 'Khoa Tiêu Hóa') — phải tồn tại trong hệ thống.
        date (str): Ngày khám theo định dạng 'dd/mm/yyyy' (Ví dụ: '29/07/2026').
        patient_name (str): Tên bệnh nhân.

    Returns:
        str: Xác nhận đặt lịch thành công kèm mã lịch hẹn, hoặc chuỗi báo lỗi
             nếu khoa không tồn tại, ngày sai định dạng/không hợp lệ, hoặc đã hết slot trống.
    """
    if department not in DEPARTMENT_SLOTS:
        valid = ", ".join(DEPARTMENT_SLOTS.keys())
        return f"LỖI: Khoa '{department}' không tồn tại trong hệ thống. Các khoa hợp lệ: {valid}."

    if not _DATE_RE.match(date.strip()):
        return f"LỖI: Ngày '{date}' không đúng định dạng dd/mm/yyyy."

    day, month, _year = date.strip().split("/")
    if not (1 <= int(day) <= 31) or not (1 <= int(month) <= 12):
        return f"LỖI: Ngày '{date}' không hợp lệ (ngày hoặc tháng vượt giới hạn)."

    date_key = date.strip()
    already_booked = BOOKED_SLOTS.setdefault((department, date_key), set())
    slot = next((s for s in DEPARTMENT_SLOTS[department] if s not in already_booked), None)

    if slot is None:
        return f"LỖI: {department} đã hết giờ khám trống vào ngày {date_key}. Vui lòng chọn ngày khác."

    already_booked.add(slot)
    return f"Đặt lịch thành công cho bệnh nhân {patient_name} tại {department} vào {date_key} lúc {slot}. Mã lịch hẹn: APT-{abs(hash((department, date_key, patient_name, slot))) % 10000:04d}."


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "find_department": find_department,
    "book_appointment": book_appointment,
}
