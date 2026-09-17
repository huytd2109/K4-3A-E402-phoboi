# Evidence mining — câu hỏi logistics trên Discord K4

## Phạm vi dữ liệu

- Nguồn: `data/discord-pack/k4_messages.csv`, bản xuất ngày 15/09/2026.
- Khoảng thời gian: 12/09/2026 06:57 đến 14/09/2026 23:54, giờ Việt Nam.
- Tổng cộng 1.092 tin nhắn: 779 tin do người viết và 313 tin do bot viết.
- Chỉ có các kênh công khai được chọn. Dữ liệu đã ẩn danh; không có DM và không
  phân biệt được học viên với TA/BTC trong trường `author`.

## Phương pháp đếm

Chạy từ thư mục gốc:

```powershell
python evidence/count_discord_evidence.py
```

Quy tắc:

1. Loại mọi dòng có `is_bot=True`.
2. Chỉ giữ tin có dấu hiệu câu hỏi như `?`, “bao giờ”, “khi nào”, “ở đâu”,
   “được không”, “cho ... hỏi” hoặc “xin”.
3. So khớp không phân biệt hoa thường với bộ từ khóa được khai báo trong script.
4. Đếm số tin, số mã tác giả khác nhau và số tin có `mentions_bot=True`.
5. Ba nhóm ứng viên độc lập; một câu hỏi hỗn hợp có thể nằm trong nhiều nhóm.

Kết quả tái lập:

| Hướng vấn đề | Tin khớp | Tác giả khác nhau | Tag bot trực tiếp |
|---|---:|---:|---:|
| Deadline, nộp bài và logistics lập đội | 14 | 12 | 7 |
| Điểm danh, XP và dữ liệu cá nhân | 22 | 17 | 14 |
| Tìm record, slide và tài liệu | 7 | 7 | 3 |

Các số trên là số quan sát trong gần ba ngày, không phải tỷ lệ đại diện cho toàn
bộ học viên. Regex có thể bỏ sót tiếng lóng hoặc bắt nhầm một số câu hỗn hợp.

## Ví dụ nguyên văn cho hướng đã chọn

1. `M19124`: “a ơi sao deadline ghép đội tự do end sớm vậy a?”
2. `M56777`: “[@BOT] hạn thành lập team là ngày nào? team không đủ 4 người có bị giải tán không”
3. `M88027`: “cho em hỏi Lab2 có được extend thời gian submit thêm không v ạ? Em lỡ nộp muộn 1 phút không submit bài được ạ”
4. `M40677`: “[@BOT] tôi nộp codelab trên vlearn đúng giờ deadline như thông báo (23:59) nhưng commit trên máy bị lỗi và sau thời gian đó mới lên thì có được tính là nộp đúng hạn không ?”
5. `M98666`: “[@BOT] thời gian mở daily standup và kết thúc là khi nào vậy? hôm qua mình gửi sớm daily standup thì không được, chiều nay quá deadline thì nó lại blocked mình.”
6. `M82163`: “[@BOT] cái daly-standup sao m ghi là hết hôm nay nhưng nộp bài thì m kêu hết hạn.”

## Diễn giải evidence

- Pain tồn tại: 14 câu hỏi logistics từ 12 tác giả trong một cửa sổ dữ liệu chưa
  đầy ba ngày; 7 câu hỏi được gửi thẳng cho bot.
- Hậu quả quan sát được: có trường hợp không nộp được vì muộn một phút
  (`M88027`), trường hợp bị block vì mốc mở/đóng không rõ (`M98666`), và trường
  hợp người học thấy hướng dẫn với trạng thái hết hạn mâu thuẫn (`M82163`).
- Chưa đo được số phút mất cho mỗi lần và chưa có khảo sát ≥20 người. Nhóm không
  dùng số liệu suy đoán cho hai đại lượng này.
