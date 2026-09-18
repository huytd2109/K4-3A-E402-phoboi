# Bộ nguồn logistics demo K4

`synthetic_sources.json` gồm **23 bản ghi**, mở rộng từ 5 bản ghi mẫu ban đầu,
cho Lab 1–6 và Daily Standup. Tất cả deadline bổ sung là giả lập; các URL
`demo.invalid` là địa chỉ minh họa, không phải nơi nộp bài thật. Không dùng
bộ này làm bằng chứng về lịch học hoặc nguồn chính thức của khóa học.

Mỗi bản ghi tuân theo `OfficialSource`, có `source_type=synthetic_demo`,
`is_fixture=true`, cohort `K4`, phạm vi lớp `ALL` và múi giờ UTC+7.
Mỗi nhiệm vụ có nguồn riêng cho deadline, link và submission. Trường submission
hiện chỉ cung cấp URL nộp bài, chưa chứa hướng dẫn nộp chi tiết.

| Nhiệm vụ | Deadline demo | Tình huống |
|---|---|---|
| Lab 1 | 16/09/2026 23:59 | Nguồn hợp lệ |
| Lab 2 | 18/09/2026 23:59 | V2 thay thế V1 ngày 17/09 |
| Lab 3 | 20/09 và 21/09/2026 23:59 | Cố ý xung đột, cần TA xác nhận |
| Lab 4 | 22/09/2026 23:59 | Nguồn hợp lệ |
| Lab 5 | 24/09/2026 23:59 | Nguồn hợp lệ |
| Lab 6 | 26/09/2026 23:59 | Nguồn hợp lệ |
| Daily Standup | 18/09/2026 22:00 | Một lần nộp giả lập, không phải lịch lặp hằng ngày |

## Dùng với ứng dụng

Trong terminal chạy backend, đặt biến môi trường rồi khởi động backend
(dừng backend cũ nếu cổng 8787 đang được dùng):

```powershell
$env:APP_ENV = "demo"
$env:SOURCE_MODE = "synthetic_demo"
$env:PYTHONPATH = "src"
python -m phoboi.api
```

Giữ cấu hình model/API key hiện có trong `.env`. Backend vẫn gọi model thật;
bộ nguồn demo không bỏ qua lỗi quota 429. Các câu trả lời từ bộ nguồn này có
badge `DỮ LIỆU DEMO`. Chế độ production/dataset không tải bộ nguồn demo.

## Câu hỏi thử

| Câu hỏi | Kết quả policy mong đợi khi phân loại đúng |
|---|---|
| Hạn nộp Lab 2 là khi nào? | Deadline V2 ngày 18/09, badge demo |
| Cho mình link nộp Lab 4? | Link minh họa LAB_04 |
| Nộp Daily Standup ở đâu? | Link minh họa DAILY_STANDUP |
| Cách nộp Lab 6? | URL nộp bài minh họa LAB_06 |
| Daily Standup hạn nộp khi nào? | 22:00 ngày 18/09, badge demo |
| Lab 3 deadline? | HANDOFF_CONFLICT |
| Lab 99 deadline? | HANDOFF_NO_SOURCE |
| Hạn nộp lab khi nào? | Hỏi lại nhiệm vụ/Lab |
