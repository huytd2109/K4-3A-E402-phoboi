# Validation kết quả cục bộ

- Thời điểm UTC: `2026-09-18T04:00:20.074016+00:00`
- Git HEAD: `4f4130d03e14222d2ec7411bdf7549beba1ee2cc`; trạng thái worktree: [git-status.txt](results/git-status.txt).
- Kết quả: **PASS** trong phạm vi offline/local.
- Pytest: 43 tests; 0 failures; 0 errors; 0 skipped.
- Số request đến model trong lần chạy này: **0**. Backend và UI không được khởi động.
- Phản hồi người test thật: [USER_FEEDBACK.md](USER_FEEDBACK.md).

| Kiểm tra | Kết quả | Bằng chứng |
|---|---|---|
| pytest | PASS | [results/pytest.log](results/pytest.log) |
| demo-data | PASS | [results/demo-data.json](results/demo-data.json) |
| typecheck | PASS | [results/typecheck.log](results/typecheck.log) |
| build | PASS | [results/build.log](results/build.log) |

## Phạm vi và giới hạn

- Quota 429: exception SDK giả lập, xác nhận lời nhắn và không tạo decision/handoff.
- Hội thoại: kiểm thử API handler với bộ phân loại deterministic; kiểm tra nối tiếp Lab 6,
  tách phiên, đổi chủ đề, TTL, giới hạn phiên/lịch sử và giữ trạng thái sau 429.
- Dữ liệu: 23 nguồn demo được kiểm tra schema, ID, nhãn fixture và 21 cặp nhiệm vụ/loại câu hỏi.
- UI: TypeScript và production build; không phải kiểm thử trình duyệt tự động.
- Kết quả này không chứng minh độ chính xác của model live, quota thật hoặc gửi handoff Discord thật.
- Deadline/link trong fixture là giả lập, không xác nhận thông tin khóa học thật.
- Không thay thế hoặc ghi đè golden evaluation trong `eval/results/latest.*`.

Xem [hướng dẫn và checklist](README.md) để chạy lại và kiểm tra thủ công.
