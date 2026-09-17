# ADR 002: Không sử dụng LLM để sinh nội dung Deadline

## Bối cảnh
Việc báo sai deadline mang lại hậu quả rất lớn cho học viên (Cost-of-error is high).

## Quyết định
Tuyệt đối **KHÔNG** sử dụng LLM để sinh ra nội dung hoặc mốc thời gian deadline.

## Lý do (Rationale)
- Hậu quả lớn: Nếu bot hallucinate deadline, học viên có thể trễ hạn nộp bài.
- Vai trò của LLM (trong tương lai) chỉ giới hạn ở việc **phân loại ý định (intent classification)**.
- Kết xuất kết quả (Rendering) phải dựa trên **Template-based** từ dữ liệu của Official Sources. Điều này đảm bảo bot chỉ cung cấp thông tin chính xác 100% từ BTC.
