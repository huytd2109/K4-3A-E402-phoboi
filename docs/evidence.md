# Phân tích dữ liệu Logistics (Evidence)

## Nguồn dữ liệu
Dữ liệu được khai thác từ `k4_messages.csv` (K4 cohort onboarding, 12-14/09/2026). Các số liệu dưới đây là số đếm tổng hợp.

## Key Findings
- Tổng số tin nhắn: **1092** (779 người dùng, 313 bot).
- Số lần nhắc đến bot: **307** tin nhắn → Bot được sử dụng rất nhiều.
- Channel hoạt động mạnh nhất: **Channel_10** (654 tin nhắn).
- Khảo sát (22 phản hồi): Đa số học viên tìm kiếm thông tin logistics 3-10+ lần/tuần.
- Nỗi đau chung (Common pain): Nhầm lẫn deadline, phải check nhiều nguồn, tốn 5-20 phút cho mỗi lần tìm kiếm.
- Báo cáo lỗi hàng ngày cho thấy các lỗi bot thực tế: injection chuỗi 'nguồn tham chiếu', cắt xén nội dung (truncation).

## Ví dụ thực tế từ dữ liệu
Dưới đây là một số ví dụ về câu hỏi logistics (trích dẫn tối đa 2 câu mỗi ví dụ):

- **M19124**: "a ơi sao deadline ghép đội tự do end sớm vậy a?"
- **M33002**: "Hạn tìm đồng đội đến bao giờ thế mọi người ơi!!!"
- **M94349**: "anh ơi cho em hỏi các buổi workshop có thể xem lại record ở đâu vậy ạ?"
- **M24139**: "Cho em xin Sổ Tay Học Viên lv 2 lúc sáng ạ"
- **M67980**: "Hôm điền form thông tin thì e ko có xe nên đã chọn đi bus... phần thẻ ra vào phải xử lý như thế nào ạ"
