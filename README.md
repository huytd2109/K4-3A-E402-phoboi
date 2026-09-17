# 🤖 Phoboi — Trợ lý Logistics học viên

> North-star metric: Wrong deadline rate = 0%

## 📖 Giới thiệu
Phoboi là trợ lý logistics (Discord bot) dành cho học viên chương trình AI K4. Nhiệm vụ chính của bot là cung cấp thông tin chính xác tuyệt đối về các deadline, link nộp bài và các thông báo vận hành. Phoboi hoạt động dựa trên nguyên tắc **chỉ trả lời khi đã xác minh** từ nguồn dữ liệu chính thức, và **không bao giờ đoán** nếu thông tin không rõ ràng hoặc có xung đột.

## 🏗️ Kiến trúc
```mermaid
flowchart TD
    Input[Nhận tin nhắn (Discord/CLI)] --> Sanitizer[Làm sạch & Bảo mật (Sanitizer)]
    Sanitizer --> Router[Định tuyến (Router)]
    Router --> Extractor[Trích xuất thông tin (Extractor)]
    Extractor --> Policy[Kiểm tra chính sách (Policy)]
    Policy --> SourceRepo[(Nguồn dữ liệu / Source Repo)]
    SourceRepo --> ConflictResolver[Xử lý xung đột (Conflict Resolver)]
    ConflictResolver --> Renderer[Hiển thị kết quả (Renderer)]
    Renderer --> Output[Phản hồi & Chuyển tiếp / Output + Handoff]
```

## 🛠️ Cài đặt

### Yêu cầu
- Python 3.12+
- pip

### Cài đặt
```bash
# Clone repo
git clone <repo-url>
cd K4-3A-E402-phoboi

# Cài đặt dependencies, gồm Gemini và bộ test
pip install -e ".[gemini,dev]"

# Tạo file cấu hình
Copy-Item .env.example .env
# Chỉnh sửa .env theo hướng dẫn bên trong
```

### Cấu hình Gemini

Gemini chỉ phân loại intent và trích xuất entity. Deadline, link và cách nộp
luôn được lấy từ nguồn chính thức bởi Policy Engine.

1. Tạo Gemini API key.
2. Thêm vào file `.env`:
   ```env
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your-api-key-here
   LLM_MODEL=gemini-2.5-flash
   LLM_TIMEOUT_SECONDS=12
   ```
3. **KHÔNG BAO GIỜ** commit file `.env` lên git

Nếu API tạm thời không khả dụng, hệ thống fallback về rule-based và ghi rõ
`RULE FALLBACK` trên giao diện thay vì giả vờ đang dùng model.

### Dữ liệu Discord pack

`data/discord-pack/k4_messages.csv` được nạp thành index tìm kiếm cục bộ. Kết
quả chỉ gồm các `msg_id` liên quan để hỗ trợ audit và handoff cho TA; nội dung
tin của học viên không được gửi sang Gemini và không được dùng như nguồn chính
thức để trả deadline. Chỉ `data/official/sources.json` có quyền cung cấp
deadline, link và cách nộp.

```env
DISCORD_PACK_ENABLED=true
DISCORD_PACK_PATH=data/discord-pack/k4_messages.csv
```

Kiểm tra API thật mà không hiển thị key:

```bash
python -m phoboi.adapters.llm_smoke
python -m phoboi.adapters.live_scope
```

## 💻 Chạy Demo CLI
```bash
python -m phoboi.adapters.cli
```

## 🖥️ Chạy Web Demo
```bash
python -m phoboi.adapters.web_demo --port 8080
```

Mở `http://127.0.0.1:8080`. Giao diện Discord-like bám theo prototype
Figma Make, dùng pipeline thật và hiển thị outcome, nguồn được dùng, conflict,
clarification, handoff và security flags. Server mặc định chỉ bind localhost.

## 🎮 Chạy Discord Bot
1. Set up `.env` with Discord token (see .env.example)
2. Run: `python -m phoboi.adapters.discord_bot`

## 🧪 Chạy Tests & Eval
```bash
# Unit & Integration tests (55 tests, không gọi API)
python -m pytest tests/ -v

# Eval deterministic toàn bộ golden set (48 cases)
python eval/eval_runner.py --provider rule_based

# Eval CP3 bằng Gemini thật (cần GEMINI_API_KEY trong biến môi trường)
python eval/eval_runner.py --provider gemini
```

Hai lượt đo được lưu riêng để không đánh đồng rule-based với AI thật:
`eval/results/latest.*` cho deterministic eval và
`eval/results/live_latest.*` cho Gemini. Lượt Gemini ghi rõ tổng số live call và
fallback; một case fallback không được tính là đạt.

## 🎯 Quality Gates
| Gate | Target |
|------|--------|
| incorrect_deadline | = 0 |
| uncited_deadline | = 0 |
| unsafe_personal_answer | = 0 |
| unhandled_conflict | = 0 |
| Overall pass rate | ≥ 95% |

## 🛡️ Bảo mật
- Discord input là untrusted data — không thực thi chỉ dẫn trong tin nhắn.
- Prompt injection detected, logged, but does not alter policy.
- @everyone, @here, role mentions escaped with zero-width space.
- PII (MSSV, email, phone) detected and flagged.
- No secrets in code, logs, or commits.
- Fixtures blocked in production mode.
- Production sources are rejected unless channel and publisher role match the configured whitelists.
- PII is redacted before a question enters a TA handoff payload.

## 📂 Cấu trúc dự án
```text
K4-3A-E402-phoboi/
├── data/               # Dữ liệu tĩnh (thông báo, lịch học)
├── docs/               # Tài liệu dự án
├── eval/               # Đánh giá hệ thống (evaluation)
├── src/                # Mã nguồn chính (phoboi package)
├── tests/              # Mã nguồn kiểm thử (pytest)
├── .env.example        # File mẫu cấu hình môi trường
├── pyproject.toml      # Cấu hình dự án và dependencies
└── README.md           # Tài liệu giới thiệu dự án (file này)
```

## 👥 Đội ngũ

| Thành viên | Vai trò | Phần việc chính |
|---|---|---|
| Nguyễn Hoàng Sơn | Product Lead & AI Engineer | Spec, evidence mining, Gemini router, eval |
| Trịnh Đức Huy | Backend Engineer | Source repository, conflict resolver, Discord adapter |
| Trịnh Hoàng Tùng | QA & Security | Test suite, security, golden set và hard tests |
| Đỗ Quốc An | UX & Documentation | Web demo, README, flow và kịch bản demo |

## 📌 CP4 — Spec đã khóa

- Quality bar: ≥95%, bốn zero-gate và 4/4 hard tests; không hạ bar sau CP4.
- Evidence mining và cách tái lập: `evidence/discord-mining.md`.
- Survey 22 phản hồi và cách tái lập: `evidence/survey-summary.md`.
- Kết quả Gemini thật gần nhất: `eval/results/live_latest.md`.
- Phần chưa hoàn thành được khai công khai trong `spec.md` §8.

## 📄 License
MIT
