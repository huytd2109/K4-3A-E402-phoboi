# AI SPEC — Verified Logistics Assistant · Nhóm phoboi · Track B1

## §1. User & Job

- User: học viên hỏi logistics; TA/Mod nhận handoff khi bot không thể xác minh.
- JTBD: khi cần biết deadline/link/cách nộp, học viên muốn nhận thông tin có thể truy nguồn hoặc biết ngay ai sẽ tiếp quản, để không hành động theo deadline bị đoán.
- Evidence: pack 1.092 tin, 779 human/313 bot; 307 human message mention bot. Mining reproducible và ví dụ theo `msg_id` ở `docs/evidence.md`.

## §2. Impact & quyết định chọn

| Ứng viên | Evidence trong 779 human | Cost-of-error | Quyết định |
|---|---:|---|---|
| Deadline/submission | 10 deadline; 17 submission | Cao: nộp muộn/sai | Chọn |
| Điểm danh/XP cá nhân | 37 attendance; 32 XP | Cao về privacy/authorization | Chặn và route support |
| Daily digest | 4 baseline reports | Trung bình; lát cắt lớn | Loại khỏi MVP |

Chọn deadline verified-source-first vì error cost cao và có thể kiểm chứng bằng source contract; không biến real pack thành knowledge base.

## §3. Giải pháp tương tự

- Discord search/bot: nhanh nhưng chat người dùng không đủ authority; sản phẩm này thêm whitelist/provenance contract và resolver.
- FAQ/RAG bot: retrieval rộng nhưng dễ coi retrieved text là fact; sản phẩm này khóa `ANSWER_VERIFIED` bằng deterministic policy.

## §4. Thiết kế

- Lát cắt: một học viên hỏi deadline một task cụ thể; AI trích intent/entity; code chỉ trả khi có đúng nguồn hợp lệ, nếu không clarify/handoff.
- Non-goals: không truy vấn điểm danh/XP/điểm; không quyết định gia hạn; không DM; không daily digest; không triển khai official Discord store trong hackathon.
- Prototype: working CLI/batch/eval + clickable UI; live provider code có thật nhưng chưa được gọi vì thiếu key.
- Automation: conditional. AI augment classification; deterministic policy giữ quyền quyết định cuối.

| Nguyên tắc | Áp dụng |
|---|---|
| Make clear what system can do | Outcome/badge rõ, real vs candidate vs demo tách biệt |
| Support efficient correction | Clarify đúng một câu |
| Mitigate social bias | Student chat không trở thành evidence |
| Fail safely | Missing/conflict/schema/provider error đều handoff/fail-closed |

## §5. Kiểu lỗi

| Lớp | Kịch bản | Kết quả |
|---|---|---|
| Input | Thiếu task | `CLARIFY` một câu |
| Input | Injection + deadline | Flag injection, vẫn xử lý logistics |
| Model | Confidence thấp | `HANDOFF_LOW_CONFIDENCE` |
| Model | JSON/ID order sai | Fail batch/error record |
| Retrieval | Không nguồn | `HANDOFF_NO_SOURCE` |
| Retrieval | Hai deadline không supersede | `HANDOFF_CONFLICT` |
| Authorization | Điểm danh/XP/MSSV | `RESTRICT_PERSONAL` |
| Provenance | URL/bộ ID không resolve | Không thể tạo `ANSWER_VERIFIED` |

## §6. Bốn đường đi

- Happy: task rõ + synthetic source hợp lệ → `ANSWER_VERIFIED` + source + badge demo.
- Low confidence: handoff, không đoán.
- Failure/no source: handoff kèm reference/entity; dedup cooldown.
- Correction/conflict: source có `supersedes` thắng; không có quan hệ → handoff.
- Outside scope/personal: support route, không truy vấn.
- Mixed intent: learning route riêng; logistics vẫn verified-or-handoff.

## §7. Kiểm thử

- Safety bar: tất cả counter nguy hiểm bằng 0; hard tests đúng outcome 100%.
- Utility bar: golden pass ≥95%; eligible answer coverage ≥95%.
- Kết quả 17/09/2026: offline tests pass; P1 golden 48/48; eligible coverage 100%; full pack test coverage 779/779; verified from real pack 0.
- Live result: chưa đo vì thiếu `GEMINI_API_KEY`; không trộn với offline result.

## §8. Phân công & kế hoạch

Đề xuất chưa được nhóm xác nhận nằm trong `TEAMMATES.md`. Validation với willing users chưa được nhóm cung cấp nên không tuyên bố hoàn thành.

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao |
|---|---|---|
| 17/09/2026 | Thay template bằng spec sản phẩm | Đồng bộ implementation |
| 17/09/2026 | Khóa real pack thành candidate-only | Không có official provenance |
| 17/09/2026 | Thêm composite `record_id` cho 3 ID trùng | Xử lý đủ 1.092 dòng, không làm rơi dữ liệu |
| 17/09/2026 | Gắn synthetic banner cho UI/fixtures | INV-06 |
