# Survey evidence — nhu cầu tra cứu logistics

## Nguồn và phương pháp

- File gốc: `evidence/survey.csv`, sao chép nguyên vẹn từ bản xuất Google Form
  do nhóm cung cấp; SHA-256:
  `17E1084190C76656DC647F0CA66CCD73926E1FAC60452B471F7A06E918FBDC89`.
- Số phản hồi: **22**; mỗi dòng có timestamp riêng.
- Khoảng thu thập: 16/09/2026 19:05:30–19:10:44.
- Nhóm xác nhận người trả lời ở ngoài nhóm dự án. File không có cột tên, mã hoặc
  vai trò nên người kiểm tra không thể xác minh độc lập khẳng định này từ CSV.
- Tái lập số liệu bằng:

```powershell
python evidence/analyze_survey.py
```

## Kết quả

| Chỉ báo | Số người | Tỷ lệ |
|---|---:|---:|
| Cần tìm thông tin logistics ít nhất một lần trong 7 ngày | 22/22 | 100,0% |
| Cần tìm ít nhất ba lần trong 7 ngày | 19/22 | 86,4% |
| Mất ít nhất năm phút để có câu trả lời đủ chắc chắn | 19/22 | 86,4% |
| Phải kiểm tra ít nhất hai nguồn | 21/22 | 95,5% |
| Phải hỏi lại TA hoặc bạn học ít nhất một lần trong tháng | 17/22 | 77,3% |
| Chọn ít nhất một hậu quả và không đồng thời chọn “chưa từng” | 18/22 | 81,8% |
| Tin câu trả lời nhờ nguồn chính thức hoặc xác nhận TA/BTC | 17/22 | 77,3% |
| Muốn handoff hoặc clarify khi hệ thống không có nguồn rõ | 13/22 | 59,1% |

Theo tiêu chí bảo thủ nhất dùng cho pain confirmation, **18/22 người (81,8%)**
chọn ít nhất một hậu quả và không có lựa chọn tự mâu thuẫn. Kết quả vượt ngưỡng
50% của đường khảo sát.

## Giới hạn chất lượng dữ liệu

- Không có tên/mã/vai trò người trả lời; chỉ có timestamp. Vì vậy CSV không tự
  chứng minh 22 người là ngoài nhóm.
- Câu 7 và Câu 12 chỉ có 1/22 câu trả lời mở. File không đủ để trích năm quote
  định tính từ survey; năm quote trong spec vẫn lấy từ Discord mining.
- Ba phản hồi ở Câu 9 vừa chọn hậu quả vừa chọn “Chưa từng gặp vấn đề”. Các dòng
  này bị loại khỏi chỉ báo xác nhận pain 18/22.
- Câu 6 cho thấy 22/22 chọn tần suất gặp thông tin mâu thuẫn, nhưng Câu 7 hầu như
  trống; không dùng Câu 6 làm chỉ báo chính.
- Toàn bộ phản hồi được ghi trong khoảng hơn năm phút. Đây có thể là một phiên
  thu tập trung; không suy rộng kết quả ra toàn bộ khóa học.
