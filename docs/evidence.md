# Phân tích dữ liệu Logistics (Evidence)

## Nguồn dữ liệu
Dữ liệu được khai thác từ `k4_messages.csv` (K4 cohort onboarding, 12-14/09/2026). Các số liệu dưới đây là số đếm tổng hợp.

## Phương pháp đếm có thể tái lập
- Đọc CSV bằng `csv.DictReader` với encoding `utf-8-sig`.
- Tổng tin = số row dữ liệu, không tính header.
- Tin bot/người = đếm `is_bot == true/false`; mention bot = đếm
  `mentions_bot == true`; tác giả = số giá trị `author` duy nhất.
- Kết quả kiểm lại ngày 17/09/2026: 1.092 row, 313 bot, 779 người,
  307 mention bot, 202 tác giả ẩn danh; `channel_10` có 654 tin.
- Không in hàng loạt `content` và không dùng CSV này làm nguồn deadline chính thức.

## Key Findings
- Tổng số tin nhắn: **1092** (779 người dùng, 313 bot).
- Số lần nhắc đến bot: **307** tin nhắn → Bot được sử dụng rất nhiều.
- Channel hoạt động mạnh nhất: **Channel_10** (654 tin nhắn).
- Repo hiện không chứa dữ liệu khảo sát có thể kiểm lại. Vì vậy không dùng các số liệu
  "22 phản hồi", "3-10+ lần/tuần" hoặc "5-20 phút" làm bằng chứng đã xác minh.
- Pain point có thể kiểm lại từ pack: học viên hỏi lặp về deadline, nơi nộp,
  ghép đội và quy định nộp muộn; bản tin bot cũng ghi nhận câu trả lời tự động
  chưa phải hướng dẫn chính thức.
- Báo cáo lỗi hàng ngày cho thấy các lỗi bot thực tế: injection chuỗi 'nguồn tham chiếu', cắt xén nội dung (truncation).

## Ví dụ thực tế từ dữ liệu
Dưới đây là một số ví dụ về câu hỏi logistics (trích dẫn tối đa 2 câu mỗi ví dụ):

- **M19124**: "a ơi sao deadline ghép đội tự do end sớm vậy a?"
- **M33002**: "Hạn tìm đồng đội đến bao giờ thế mọi người ơi!!!"
- **M94349**: "anh ơi cho em hỏi các buổi workshop có thể xem lại record ở đâu vậy ạ?"
- **M24139**: "Cho em xin Sổ Tay Học Viên lv 2 lúc sáng ạ"
- **M67980**: "Hôm điền form thông tin thì e ko có xe nên đã chọn đi bus... phần thẻ ra vào phải xử lý như thế nào ạ"
