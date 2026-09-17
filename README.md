# Phoboi — Verified Logistics Assistant

Prototype trợ lý Discord trả lời logistics theo nguyên tắc **verified-source-first**: AI chỉ phân loại intent và trích entity; code deterministic quyết định có được trả lời hay phải làm rõ/chuyển TA. LLM không viết deadline, URL nguồn hoặc chính sách nộp muộn.

## Trạng thái bàn giao

- P0 core, CLI, source policy, hard tests và Demo DoD: hoàn thành; offline tests 29/29.
- P1 batch/checkpoint/report: đã xử lý 1.092 dòng bằng chế độ test (779/779 human, 0 error); golden set 48/48, eligible coverage 100%.
- P2 provider adapters, Discord adapter và UI React: đã có; Discord thật chưa kết nối vì không có token/ID thật (ngoài phạm vi dữ liệu được cấp).
- Live Gemini preflight/batch/eval: **chưa thể chạy vì môi trường chưa có `GEMINI_API_KEY`**. Live mode fail-closed, không fallback sang mock. Xem [BLOCKERS.md](BLOCKERS.md).

Các con số offline chứng minh policy/pipeline, không phải bằng chứng live AI.

## Ba nhãn dữ liệu

| Nhãn | Nghĩa | Có thể tạo `ANSWER_VERIFIED`? |
|---|---|---:|
| `REAL DATA` | Tin Discord đã ẩn danh trong pack | Không |
| `UNVERIFIED CANDIDATE` | Fact trích từ real pack nhưng không có official provenance | Không |
| `SYNTHETIC DEMO SOURCE` / `DỮ LIỆU DEMO` | Fixture kiểm soát để chứng minh happy path | Có, chỉ ở `SOURCE_MODE=synthetic_demo` |

Deadline xuất hiện trong UI/fixture đều là dữ liệu tổng hợp, không phải thông tin khóa học thật.

## Cài đặt

Python 3.12+ được khuyến nghị; code hiện tương thích 3.10+ vì máy hackathon chỉ có Python 3.10.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Không điền secret vào repo. `.env` và `runs/` đã được ignore.

## Chạy offline tests và demo

```powershell
$env:APP_ENV = "test"
$env:SOURCE_MODE = "dataset"
python -m pytest

# Demo fixture, không gọi API và luôn có badge DỮ LIỆU DEMO
python -m phoboi chat --source-mode synthetic-demo --message "Lab 2 deadline?"
python -m phoboi chat --source-mode synthetic-demo --message "Hạn nộp lab khi nào?"
python -m phoboi chat --source-mode synthetic-demo --message "Lab 3 deadline?"  # conflict demo
python -m phoboi chat --source-mode synthetic-demo --message "Lab 99 deadline?" # no source demo
python -m phoboi chat --source-mode synthetic-demo --message "Điểm danh của tôi thế nào?"

# Real pack boundary: không bao giờ verified
python -m phoboi chat --source-mode dataset --message "Lab 2 deadline?"
```

Offline classifier chỉ được phép khi `APP_ENV=test`. `demo` và `production` luôn cần live provider.

## Chạy live Gemini

Điền `GEMINI_API_KEY` trong `.env`, không đưa key lên terminal/log:

```powershell
$env:APP_ENV = "production"
$env:SOURCE_MODE = "dataset"
python -m phoboi preflight --require-live
python -m phoboi analyze-data --input data/discord-pack/k4_messages.csv --require-live --resume
python -m phoboi report --run latest

$env:APP_ENV = "demo"
$env:SOURCE_MODE = "synthetic_demo"
python -m phoboi chat --require-live --source-mode synthetic-demo
python -m phoboi eval --suite golden --require-live
```

`--require-live` trả exit code khác 0 khi thiếu key, API/schema lỗi, không có live response hoặc batch bỏ sót human row. Ước tính full pack với batch 20 là 39 request; CLI luôn in estimate trước khi chạy.

Provider khác dùng `LLM_PROVIDER=openrouter|openai|anthropic`, `LLM_MODEL` và key tương ứng. Cài optional SDK trước khi dùng, ví dụ `pip install -e ".[openai]"`.

## Batch artifacts

Mỗi run tạo thư mục `runs/<run_id>/` gồm:

- `manifest.json`: provider/model, live flag, dataset/prompt hash, latency/usage, không có secret.
- `classifications.jsonl`, `policy_decisions.jsonl`, `errors.jsonl`: dùng `record_id` nội bộ để không làm rơi 3 ID bị trùng trong pack.
- `baseline_pairs.jsonl`: chỉ ID và đặc trưng aggregate, không lưu bot reply raw.
- `metrics.json`, `report.md`.

Run test đã xác nhận đủ 1.092 row nhưng nằm trong `runs/` và không commit vì có artifact vận hành. Báo cáo redacted được commit tại [eval/results/dataset_offline_validation.md](eval/results/dataset_offline_validation.md).

## UI demo

```powershell
cd web
npm install
npm run dev
# hoặc npm run build
```

UI kế thừa flow từ `phoboi-cp2.zip`: answer, clarify, resolvable/unresolved conflict, no-source, personal-data, injection và mixed intent. Banner cố định đánh dấu toàn bộ persona/source/deadline là synthetic demo.

## Discord mode

`src/phoboi/discord_adapter.py` là adapter hoàn chỉnh có thể test mà không cần token. Runtime chỉ đọc message có mention bot trong guild được cấu hình, escape mọi mention ở public reply, và chỉ cho phép mention đúng `DISCORD_TA_ROLE_ID` trong handoff path. Cần cài `discord.py` và bốn biến `DISCORD_*` trong `.env` để kết nối thật; thao tác triển khai Discord thật nằm ngoài phạm vi pack.

## Bảo mật và giới hạn

- Real pack không phải official knowledge base; deadline correctness trên pack là `unverifiable`.
- Personal request luôn bị chặn bởi LLM signal **OR** regex backstop; không truy vấn record cá nhân.
- Injection flag không loại bỏ message; phần intent hợp lệ vẫn đi qua policy bình thường.
- Handoff chỉ lưu hash/reference, entity và source ID; không lưu raw personal query.
- Không log API key, raw response, chain-of-thought hay hàng loạt nội dung Discord.
- File data đang được Git track trong repo hiện tại. Không tự xóa vì đây là dữ liệu được cấp; không public repo và tuân thủ chính sách xóa của BTC.

Chi tiết: [kiến trúc](docs/architecture.md), [source policy](docs/source-policy.md), [evidence](docs/evidence.md), [spec](spec.md).
