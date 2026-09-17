from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from phoboi.analyzer import MessageAnalyzer
from phoboi.config import Settings
from phoboi.models import AnalysisBatch
from phoboi.providers.factory import create_provider


def run_preflight(settings: Settings, *, output_dir: Path = Path("runs")) -> dict:
    provider = create_provider(settings)
    response = MessageAnalyzer(provider, model=settings.llm_model, temperature=settings.llm_temperature).analyze_batch(
        [("PREFLIGHT", "Xin chào, đây có phải trợ lý logistics không?", None)]
    )
    validated = AnalysisBatch.model_validate(response.data)
    if not response.live or response.provider != settings.llm_provider or not validated.results:
        raise RuntimeError("preflight did not return a valid live response")
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "configured": settings.api_key_configured,
        "live": response.live,
        "provider": response.provider,
        "model": response.model,
        "latency_ms": round(response.latency_ms, 2),
        "request_id_present": bool(response.request_id),
        "usage": {"input_tokens": response.input_tokens, "output_tokens": response.output_tokens},
        "schema_valid": True,
    }
    run_dir = output_dir / f"preflight-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "preflight.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report

