# Validation

Bộ kiểm tra cho xử lý quota 429, ngữ cảnh chat theo phiên, nguồn demo và giao diện.

## Chạy lại

Từ thư mục gốc dự án, dùng Python có dependencies của dự án, Node và `web/node_modules`:

```powershell
python validation/run_validation.py
```

Script không gọi provider, không đọc/in API key, không bật backend/UI. Mỗi lần chạy
ghi đè báo cáo và kết quả trong thư mục này. Exit code 0 khi mọi nhóm PASS, 1 khi
có FAIL hoặc BLOCKED. Build tạo lại `web/dist`.

## File kết quả

- `REPORT.md`: báo cáo tổng hợp và giới hạn kết luận.
- `results/summary.json`: trạng thái kiểm tra, thời điểm và Git HEAD.
- `results/pytest.xml`, `results/pytest.log`: kết quả toàn bộ test Python.
- `results/demo-data.json`: schema/nhãn dữ liệu và 21 tình huống nguồn demo.
- `results/typecheck.log`, `results/build.log`: kiểm tra giao diện.
- `results/git-status.txt`: trạng thái checkout khi bắt đầu chạy.

## Checklist thủ công — chưa chạy trong bộ validation offline này

Chỉ thực hiện sau khi bật backend demo và UI theo `fixtures/README.md`.

| Thao tác | Kỳ vọng |
|---|---|
| Hỏi “Hạn nộp lab khi nào?” | Hỏi lại tên Lab |
| Trả lời “Lab 6” | Deadline 26/09/2026 23:59, nhãn DỮ LIỆU DEMO, không handoff |
| Hỏi “Link nộp thì sao?” | Giữ task Lab 6, trả link demo tương ứng |
| Chuyển chủ đề: “Giải thích YOLO”, rồi “Lab 6” | Không kế thừa câu hỏi deadline cũ |
| Mở phiên chat mới, gửi “Lab 6” | Không lấy ngữ cảnh từ phiên trước |
| Hỏi “Lab 3 deadline?” | HANDOFF_CONFLICT |
| Hỏi “Lab 99 deadline?” | HANDOFF_NO_SOURCE |
| Model trả 429 | Lời nhắn nghỉ ngơi, không handoff; vẫn thử lại được |

Không cố gọi đến cạn quota để kiểm tra 429; tests đã giả lập lỗi này.
Checklist không phải bằng chứng đã thực hiện. Handoff ở đây là kết quả policy,
không phải xác nhận TA đã nhận thông báo Discord.
