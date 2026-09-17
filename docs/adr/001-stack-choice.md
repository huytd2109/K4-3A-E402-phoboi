# ADR 001: Lựa chọn Stack Công nghệ

## Bối cảnh
Dự án cần một tech stack đơn giản, ít phụ thuộc, có khả năng chạy offline.

## Quyết định
Sử dụng **Python 3.12 + Pydantic v2 + Rule-based Router**.

## Lý do (Rationale)
- **Python 3.12**: Hiệu năng tốt, dễ bảo trì, phổ biến trong cộng đồng AI.
- **Pydantic v2**: Đảm bảo schema validation mạnh mẽ, giúp chặn dữ liệu không hợp lệ ngay từ đầu.
- **Rule-based Router**: Không có logic phức tạp từ LLM ngay từ đầu, đảm bảo tính deterministic 100%. 
- **Offline-first**: Phù hợp cho việc xử lý các tập tin local mà không cần gọi network (ngoại trừ Discord API để đọc/ghi tin nhắn).
- Không có sẵn stack nào trong repo, nên thiết lập từ đầu với dependencies tối thiểu.
