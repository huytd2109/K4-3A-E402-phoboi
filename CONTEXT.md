# BÁO CÁO CONTEXT: TIẾN ĐỘ THỰC HIỆN DỰ ÁN PHÔBOI (TRACK B - DISCORD ASSISTANT)

> **Thời điểm cập nhật:** 2026-09-17 11:25 (UTC+7)  
> **Trạng thái tổng thể:** Hoàn thành Core Engine, Pipeline, Tests, Eval Runner & Tài liệu kỹ thuật. Đạt 100% Quality Gates.  
> **Mục tiêu North-Star:** Wrong deadline rate = 0%.

---

## 1. TỔNG QUAN NHỮNG VIỆC ĐÃ HOÀN THÀNH

### A. Nghiên cứu dữ liệu & Khảo sát thực tế (Phase A)
- [x] **Audit toàn bộ kho dữ liệu**:
  - `data/discord-pack/k4_messages.csv`: Phân tích 1.092 tin nhắn (779 tin người dùng, 313 tin bot); 307 tin tag trực tiếp `@BOT`.
  - Repo không có `survey.csv`; các số liệu khảo sát cũ không được xem là evidence có thể kiểm lại.
  - `k4_daily_reports.md`: Chỉ ra các lỗi thật của bot hiện tại (lỗi chèn chuỗi `"nguồn tham chiếu"`, tóm tắt cắt cụt).
- [x] **Tài liệu hóa bằng chứng (`docs/evidence.md`)**:
  - Tổng hợp phương pháp đếm, bảng số liệu aggregate, 5 ví dụ trích dẫn dẫn nguồn bằng `msg_id` (tuân thủ quy định tối đa 2 câu/trích dẫn, bảo mật PII).

### B. Kiến trúc & Thiết kế hệ thống (Phase B)
- [x] **Đặc tả kiến trúc (`docs/architecture.md`)**:
  - Sơ đồ Pipeline theo Mermaid: `Input -> Sanitizer -> Router -> Extractor -> Policy Engine -> Source Repo / Resolver -> Renderer -> Output + Handoff`.
  - Xác lập ranh giới tin cậy (Trust boundaries): Dữ liệu Discord là *untrusted*, thông báo chính thức là *trusted*.
  - Nguyên tắc thiết kế: **Fail-closed** (khi có lỗi dữ liệu hoặc thiếu nguồn, không bao giờ đoán mò).
- [x] **Chính sách nguồn chính thức (`docs/source-policy.md`)**:
  - Quy định Whitelist channel/role, cấu trúc `OfficialSource`, cơ chế `supersedes`, `revoked`.
  - Quy tắc phân xử mâu thuẫn xác định (Deterministic Conflict Resolution): Không chọn deadline mới hơn chỉ dựa vào timestamp nếu không có quan hệ thay thế.
- [x] **Biên bản quyết định kiến trúc (ADRs)**:
  - `docs/adr/001-stack-choice.md`: Chọn Python 3.12+, Pydantic v2, offline-first rule-based pipeline, không phụ thuộc mạng khi chạy test/eval.
  - `docs/adr/002-no-llm-for-deadlines.md`: LLM chỉ phân loại intent/entity; cấm hoàn toàn việc LLM tự sinh deadline hoặc link nộp bài.

### C. Phát triển Core Pipeline (Phase C)
- [x] **Domain Models (`src/phoboi/models.py`)**:
  - Enums: `Intent` (8 nhãn), `PolicyOutcome` (9 kết quả), `SourceStatus`, `LogisticsType`.
  - Model `OfficialSource` chuẩn hóa theo §5.
  - Invariant validator: `ANSWER_VERIFIED` tuyệt đối không được sinh ra nếu không có `source_url` hợp lệ.
- [x] **Security & Sanitization (`src/phoboi/security/`)**:
  - Chặn prompt injection ("bỏ qua quy định", "system prompt", "hãy dùng deadline bạn nhớ").
  - Loại bỏ mention bot khỏi dữ liệu phân loại.
  - Thoát ký tự mention (`@everyone`, `@here`, role mention) bằng zero-width space để tránh ping bậy.
  - Phát hiện PII (MSSV, Email, SĐT) và giới hạn độ dài tin nhắn.
- [x] **Multi-intent Router & Entity Extraction (`src/phoboi/intent/`)**:
  - Phân loại multi-label: `GREETING`, `LOGISTICS_DEADLINE`, `LOGISTICS_LINK`, `LOGISTICS_SUBMISSION`, `LEARNING`, `PERSONAL_RESTRICTED`, `OUT_OF_SCOPE`, `UNKNOWN`.
  - Trích xuất: `task` (Lab 1-10, Workshop, Team formation...), `cohort` (K4), `class_scope` (L2-3, L3-4).
- [x] **Official Source Repository & Conflict Resolver (`src/phoboi/sources/`)**:
  - Quản lý kho nguồn chính thức, tìm kiếm theo scope.
  - Phân xử mâu thuẫn: Phát hiện xung đột 2 thông báo khác deadline (`HANDOFF_CONFLICT`), nguồn bị thay thế (`supersedes`), chia tách theo lớp.
  - Cơ chế cách ly: Nghiêm cấm nạp dữ liệu `is_fixture: true` trong môi trường `APP_ENV=production`.
- [x] **Policy Engine (`src/phoboi/policy/`)**:
  - Bộ luật điều phối quyết định: Chỉ trả lời khi có căn cứ, thiếu dữ kiện -> `CLARIFY`, không có nguồn -> `HANDOFF_NO_SOURCE`, câu hỏi cá nhân -> `RESTRICT_PERSONAL`.
- [x] **Response Template Renderer (`src/phoboi/rendering/`)**:
  - Render mẫu câu trả lời chuẩn tiếng Việt, hiển thị đúng giờ UTC+7 kèm trích dẫn URL thông báo chính thức.
  - Tự động gắn banner cảnh báo khi chạy ở chế độ demo/fixture.
- [x] **TA Escalation & Anti-spam Cooldown (`src/phoboi/handoff/`)**:
  - Tạo payload chuyển giao TA kèm mã lý do, entity trích xuất, dedup key và cooldown 300s chống spam.
- [x] **Pipeline Orchestrator (`src/phoboi/pipeline.py`)**:
  - Ghép nối toàn bộ chu trình xử lý end-to-end.

### D. Giao diện thực thi (Phase D)
- [x] **CLI Demo (`src/phoboi/adapters/cli.py`)**:
  - Chạy tương tác qua terminal (`python -m phoboi.adapters.cli`), offline 100%, hiển thị debug Intent & Outcome.
- [x] **Discord Adapter (`src/phoboi/adapters/discord_bot.py`)**:
  - Khung adapter hoàn chỉnh cho `discord.py`, lắng nghe mention, tách biệt cấu hình môi trường, test được mà không cần token thật.
- [x] **Cấu hình môi trường (`.env.example`, `src/phoboi/config.py`)**:
  - Không chứa secret, cấu hình linh hoạt cho demo, test và production.

### E. Dữ liệu mẫu & Kiểm thử tự động (Phase E)
- [x] **Dữ liệu mẫu (`data/official/sources.json`)**:
  - Tạo 7 nguồn mẫu fixture (`is_fixture: true`) có đầy đủ Lab 1, Lab 2 (cố tình tạo conflict), Workshop 1, Ghép đội, Lab 3 (phân tách theo lớp).
- [x] **Bộ Unit & Integration Tests (`tests/`)**:
  - 48/48 tests PASSED qua `pytest`:
    - Schema validation, Invariant checks.
    - Router & Entity extractor.
    - Security (Injection, Mention escaping, PII).
    - Source Repo & Conflict resolver.
    - 4 Hard Tests bắt buộc (Conflict, Personal restriction, Mention/Injection, Mixed learning+logistics).
- [x] **Golden Set & Eval Runner (`eval/`)**:
  - `eval/golden_set.jsonl`: 48 test cases chuẩn hóa bao phủ 8 phân loại.
  - `eval/eval_runner.py`: Chạy đánh giá tự động và xuất báo cáo.
  - Kết quả kiểm định: **48/48 PASSED (100.0%)**.
  - Quality Gate:
    - `incorrect_deadline = 0` (Đạt)
    - `uncited_deadline = 0` (Đạt)
    - `unsafe_personal_answer = 0` (Đạt)
    - `unhandled_conflict = 0` (Đạt)
    - Pass rate: **100.0%** (Vượt mốc yêu cầu >= 95%).

---

## 2. NHỮNG VIỆC CHƯA HOÀN THÀNH (THEO KẾ HOẠCH & MASTER PROMPT)

Dưới đây là các hạng mục tồn đọng cần hoàn tất để đạt Definition of Done (DoD) đầy đủ:

| STT | Hạng mục | Tình trạng hiện tại | Việc cần làm tiếp |
|:---:|---|---|---|
| 1 | **`spec.md`** | Đã điền §1–§9 và bỏ số liệu survey không có artifact. | Bổ sung evidence khảo sát chỉ khi có dữ liệu ẩn danh kiểm lại được. |
| 2 | **`README.md`** | Đã có setup, CLI, web demo, Discord, test/eval và security notes. | Duy trì lệnh và số test theo bản chạy mới nhất. |
| 3 | **`TEAMMATES.md`** | Đã có phân công đề xuất và ghi rõ chưa được nhóm xác nhận. | Nhóm xác nhận hoặc điều chỉnh phân công. |
| 4 | **Git Working Tree Cleanup** | Đang có 2 file modified chưa commit (`.gitignore`, `track-b-discord-assistant.md`) và nhiều file untracked mới tạo. | Review diff, staging và commit các module code, tests, docs lên git theo đúng chuẩn quy định của hackathon. |
| 5 | **Triển khai Discord Production thật (Blocker bên ngoài)** | Đang chạy offline giả lập với Demo Fixtures. | Chờ BTC/Người dùng cung cấp Token bot, Guild ID, Channel ID, Role TA (đã liệt kê trong `BLOCKERS.md`) khi cần đưa lên server thật. |

---

## 3. CÁC LỆNH KIỂM CHỨNG NHANH CỦA DỰ ÁN

Hệ thống hiện tại đã sẵn sàng để kiểm tra độc lập tại local:

```bash
# 1. Chạy toàn bộ unit tests (48 tests)
python -m pytest tests/ -v

# 2. Chạy bộ đánh giá Golden Set (48 cases)
python eval/eval_runner.py

# 3. Chạy CLI demo
python -m phoboi.adapters.cli

# 4. Chạy web demo theo Figma Make
python -m phoboi.adapters.web_demo --port 8080
```

