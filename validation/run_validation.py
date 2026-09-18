"""Run local validation without starting services or calling an LLM provider."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "validation" / "results"
sys.path.insert(0, str(ROOT / "src"))


def run_command(name: str, command: list[str], cwd: Path) -> dict:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), NO_COLOR="1")
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (OUTPUT / f"{name}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    return {"name": name, "status": "PASS" if result.returncode == 0 else "FAIL", "exit_code": result.returncode, "log": f"results/{name}.log"}


def validate_sources() -> dict:
    from phoboi.models import Analysis, Entities, Intent
    from phoboi.policy import decide
    from phoboi.sources import SyntheticDemoSourceStore

    store = SyntheticDemoSourceStore()
    ids = [row.source_id for row in store.sources]
    checks = [{"case": "23 unique schema-valid demo sources", "pass": len(ids) == len(set(ids)) == 23}]
    checks.append({"case": "all sources explicitly marked as fixtures", "pass": all(s.is_fixture and s.source_type == "synthetic_demo" for s in store.sources)})
    for task in [f"LAB_{n:02d}" for n in range(1, 7)] + ["DAILY_STANDUP"]:
        for kind in ["deadline", "link", "submission"]:
            analysis = Analysis(msg_id=f"{task}-{kind}", is_question=True, intents=[Intent("LOGISTICS_" + kind.upper())], entities=Entities(task=task, cohort="K4", logistics_type=kind), confidence=1)
            decision = decide(analysis, task, store)
            expected = "HANDOFF_CONFLICT" if task == "LAB_03" and kind == "deadline" else "ANSWER_VERIFIED"
            passed = decision.outcome.value == expected
            if expected == "ANSWER_VERIFIED":
                passed = passed and decision.badge == "DỮ LIỆU DEMO" and decision.handoff is None
            checks.append({"case": f"{task}/{kind}", "expected": expected, "actual": decision.outcome.value, "pass": passed})
    (OUTPUT / "demo-data.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"name": "demo-data", "status": "PASS" if all(c["pass"] for c in checks) else "FAIL", "passed": sum(c["pass"] for c in checks), "total": len(checks), "log": "results/demo-data.json"}


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "pytest.xml").unlink(missing_ok=True)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    worktree = subprocess.run(["git", "status", "--short"], cwd=ROOT, capture_output=True, text=True).stdout
    (OUTPUT / "git-status.txt").write_text(worktree, encoding="utf-8")
    checks = [run_command("pytest", [sys.executable, "-m", "pytest", f"--junitxml={OUTPUT / 'pytest.xml'}"], ROOT)]
    if (OUTPUT / "pytest.xml").exists():
        suite = ET.parse(OUTPUT / "pytest.xml").getroot()
        checks[0]["counts"] = {key: sum(int(s.get(key, 0)) for s in suite.iter("testsuite")) for key in ["tests", "failures", "errors", "skipped"]}
    try:
        checks.append(validate_sources())
    except Exception as exc:
        checks.append({"name": "demo-data", "status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})
    node = shutil.which("node")
    for name, entry, arguments in [
        ("typecheck", "node_modules/typescript/bin/tsc", ["--noEmit"]),
        ("build", "node_modules/vite/bin/vite.js", ["build"]),
    ]:
        if node and (ROOT / "web" / entry).exists():
            checks.append(run_command(name, [node, entry, *arguments], ROOT / "web"))
        else:
            checks.append({"name": name, "status": "BLOCKED", "reason": "Node or web dependencies are missing"})
    passed = all(c["status"] == "PASS" for c in checks)
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "git_head": revision, "mode": "offline_local", "live_provider_requests": 0, "status": "PASS" if passed else "FAIL", "checks": checks}
    (OUTPUT / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = "\n".join(f"| {c['name']} | {c['status']} | [{c['log']}]({c['log']}) |" if "log" in c else f"| {c['name']} | {c['status']} | Xem results/summary.json |" for c in checks)
    counts = checks[0].get("counts", {})
    markdown = f"""# Validation kết quả cục bộ

- Thời điểm UTC: `{report['generated_at']}`
- Git HEAD: `{revision}`; trạng thái worktree: [git-status.txt](results/git-status.txt).
- Kết quả: **{report['status']}** trong phạm vi offline/local.
- Pytest: {counts.get('tests', '?')} tests; {counts.get('failures', '?')} failures; {counts.get('errors', '?')} errors; {counts.get('skipped', '?')} skipped.
- Số request đến model trong lần chạy này: **0**. Backend và UI không được khởi động.

| Kiểm tra | Kết quả | Bằng chứng |
|---|---|---|
{rows}

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
"""
    (ROOT / "validation" / "REPORT.md").write_text(markdown, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
