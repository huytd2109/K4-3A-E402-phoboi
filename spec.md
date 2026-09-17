# AI Spec - Dự án phoboi (K4-3A-E402)

**Thông tin dự án:**
- **Nhóm:** phoboi (Group E402, Zone 3A)
- **Track:** B — Trợ lý Học viên (Discord Assistant)
- **Loại:** Tối ưu tính năng có sẵn
- **Thành viên:** Nguyễn Hoàng Sơn, Trịnh Đức Huy, Trịnh Hoàng Tùng, Đỗ Quốc An

## §1. Người Dùng và Công Việc (User & Job)
- **Người thực thi công việc (Job executor):** Học viên K4 (AI program, VinUni)
- **Core JTBD:** "Khi cần nộp bài đúng hạn, tôi muốn tìm được deadline chính xác từ một nguồn tin cậy, để không bị trễ hạn và không phải tự suy đoán giữa nhiều thông báo."
- **Vấn đề cốt lõi (Problem statement):** "Học viên phải hỏi lại về deadline và nơi nộp khi thông tin nằm rải rác hoặc câu trả lời tự động chưa phải hướng dẫn chính thức."
- **Bằng chứng (Evidence):**
  - **Data mining (k4_messages.csv):** 1.092 tin nhắn (779 người, 313 bot), 307 tin tag bot trực tiếp.
  - **Giới hạn evidence:** repo không chứa `survey.csv`; không dùng số liệu khảo sát chưa thể kiểm lại.
  - **5 quotes with msg_id:**
    1. M19124: "a ơi sao deadline ghép đội tự do end sớm vậy a?"
    2. M33002: "Hạn tìm đồng đội đến bao giờ thế mọi người ơi!!!"
    3. M94349: "anh ơi cho em hỏi các buổi workshop có thể xem lại record ở đâu vậy ạ?"
    4. M24139: "Cho em xin Sổ Tay Học Viên lv 2 lúc sáng ạ"
    5. M67980: "Hôm điền form thông tin thì e ko có xe nên đã chọn đi bus..."

## §2. Tác Động và Quyết Định Chọn (Impact & Decision)
3 phương án đã được đánh giá:
1. **Dashboard tổng hợp deadline (web)** — LOẠI vì tạo thêm nơi học viên phải kiểm tra và nằm ngoài lát cắt Discord.
2. **Trợ lý deadline verified-only (Discord bot)** — CHỌN vì giải quyết trực tiếp câu hỏi deadline với nguyên tắc verified-or-handoff.
3. **Daily digest tự động** — LOẠI vì không giải quyết trực tiếp câu hỏi theo yêu cầu và là non-goal của MVP.

## §3. Giải Pháp Tương Tự
- **Notion Calendar Bot:** auto-sync nhưng thiếu verified source. *Đáng học:* UI rõ ràng; *Đáng né:* không có conflict detection; *Khác biệt:* phoboi verify nguồn gốc.
- **Duolingo Reminder Bot:** nhắc nhở liên tục. *Đáng học:* ngắn gọn; *Đáng né:* spam; *Khác biệt:* phoboi chỉ trả lời khi được hỏi.

## §4. Thiết Kế
- **Lát cắt:** "Một học viên hỏi deadline một nhiệm vụ cụ thể → bot trả lời verified-only từ nguồn chính thức kèm link, hoặc chuyển TA nếu không chắc chắn."
- **Non-goals:** (1) Không xem/trả lời điểm danh, XP, tài khoản cá nhân. (2) Không tự quyết gia hạn/châm chước. (3) Không DM học viên. (4) Không làm daily digest.
- **Prototype:** Working — toàn bộ core pipeline, CLI demo, Discord adapter, eval 48 cases.
- **Automation:** Augment — cost-of-error cao (sai deadline = trễ nộp), nên bot chỉ trả lời khi verified, chuyển người (handoff) khi không chắc chắn.

**§4b Nguyên Tắc Thiết Kế (Principles):**
| Nguyên tắc | Áp dụng cụ thể |
|---|---|
| G1 — Make clear what the system can do | Bot chào hỏi kèm scope: "giúp về deadline, link, cách nộp" |
| G2 — Make clear how well the system can do it | Chỉ trả lời verified, từ chối đoán, banner demo khi dùng fixture |
| G10 — Scope services when in doubt | Thiếu 1 entity → hỏi clarify đúng 1 câu, không gộp/đoán |
| G11 — Make clear why the system did what it did | Mỗi answer kèm URL nguồn chính thức |
| PAIR-6 — Fail gracefully | No source → handoff TA, Conflict → handoff TA, không bao giờ bịa |
| HAX-14 — Support efficient correction | Pipeline audit log cho TA review và sửa |

## §5. Kiểu Lỗi — 4 Lớp + 8 Kịch Bản
| Lớp | Kịch bản | Hành vi |
|---|---|---|
| Sai nội dung | Bot đoán sai deadline | Không xảy ra: LLM cấm sinh deadline, chỉ template từ source |
| Sai nội dung | Bot trộn deadline 2 lớp | Yêu cầu clarify class_scope |
| Thiếu/bỏ sót | Không có nguồn cho task | HANDOFF_NO_SOURCE → chuyển TA |
| Thiếu/bỏ sót | Thiếu entity (task, cohort) | CLARIFY → hỏi đúng 1 câu |
| Quá phạm vi | Hỏi điểm danh/XP cá nhân | RESTRICT_PERSONAL → hướng dẫn kênh riêng |
| Quá phạm vi | Câu hỏi bài học thuần | ROUTE_LEARNING → gợi ý hỏi TA |
| Bảo mật | Prompt injection | Phát hiện, ghi audit, vẫn xử lý câu hỏi hợp lệ |
| Bảo mật | Mention injection @everyone | Escape bằng zero-width space |

## §6. Bốn Đường Đi (Paths)
- **Happy path:** Hỏi "deadline lab 1" → ANSWER_VERIFIED với thời gian, link nguồn, link nộp.
- **Low-confidence:** Thiếu task → CLARIFY hỏi 1 câu; Thiếu class → CLARIFY class_scope.
- **Failure/không căn cứ:** Không tìm được nguồn → HANDOFF_NO_SOURCE chuyển TA; 2 nguồn mâu thuẫn → HANDOFF_CONFLICT chuyển TA.
- **Correction:** TA review handoff, cập nhật official source, bot tự lấy nguồn mới.
- **Ngoài phạm vi:** Điểm danh → RESTRICT_PERSONAL; Bài học → ROUTE_LEARNING; Random → OUT_OF_SCOPE.
- **Case đặc thù:** Mixed intent (hỏi bài + deadline) → tách riêng, logistics verified-or-handoff.

## §7. Kiểm Thử (Testing)
- **Quality dimensions:** Correctness (wrong deadline = 0), Safety (no PII leak), Robustness (injection handled).
- **Golden set:** 48 cases trong `eval/golden_set.jsonl` (12 single source, 8 no source, 6 missing entity, 6 conflict, 4 personal, 4 injection, 4 mixed, 4 greeting/oos).
- **Quality bar:** "Đạt khi ≥ 95% qua bộ, incorrect_deadline = 0, uncited_deadline = 0, unsafe_personal = 0, unhandled_conflict = 0, 4 hard tests pass 100%."
- **Results:** cập nhật tự động trong `eval/results/latest.md`; không dùng báo cáo cũ thay cho lần chạy hiện tại.

## §8. Phân Công Trách Nhiệm
| Thành viên | Vai trò | Phần việc chính |
|---|---|---|
| Nguyễn Hoàng Sơn | Product Lead & AI Engineer | Spec, Evidence mining, Core pipeline, Eval |
| Trịnh Đức Huy | Backend Engineer | Source repo, Conflict resolver, Discord adapter |
| Trịnh Hoàng Tùng | QA & Security | Test suite, Security module, Golden set |
| Đỗ Quốc An | UX & Documentation | Docs, README, CLI demo, UI mockup |

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao |
|---|---|---|
| 2026-09-15 | Khởi tạo spec template | Bắt đầu dự án theo track B |
| 2026-09-16 | Mining evidence + survey | Xác nhận pain point từ data thực tế |
| 2026-09-17 | Hoàn thiện pipeline + eval 100% | Đạt quality gate, sẵn sàng demo |
| 2026-09-17 | Điền đầy đủ spec §1-§9 | Chuẩn bị nộp trước hạn chốt 21:00 |
| 2026-09-17 | Bỏ số liệu survey không có artifact kiểm chứng | Giữ evidence có thể tái lập từ repo |
| 2026-09-17 | Đồng bộ web demo theo Figma Make và siết policy | Hoàn thiện demo end-to-end, whitelist, scope và handoff |
