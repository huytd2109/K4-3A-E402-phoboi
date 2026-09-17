from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    app_env: str
    source_mode: str
    llm_provider: str
    llm_model: str
    llm_temperature: float
    llm_batch_size: int
    llm_max_retries: int
    request_timeout_seconds: float
    max_concurrency: int

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv()
        settings = cls(
            app_env=os.getenv("APP_ENV", "production"),
            source_mode=os.getenv("SOURCE_MODE", "dataset"),
            llm_provider=os.getenv("LLM_PROVIDER", "gemini"),
            llm_model=os.getenv("LLM_MODEL", "gemini-2.5-flash"),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0")),
            llm_batch_size=int(os.getenv("LLM_BATCH_SIZE", "20")),
            llm_max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            request_timeout_seconds=float(os.getenv("LLM_REQUEST_TIMEOUT_SECONDS", "60")),
            max_concurrency=int(os.getenv("LLM_MAX_CONCURRENCY", "1")),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.app_env not in {"test", "demo", "production"}:
            raise ValueError("APP_ENV must be test, demo, or production")
        if self.source_mode not in {"dataset", "synthetic_demo", "official_discord"}:
            raise ValueError("invalid SOURCE_MODE")
        if self.app_env == "demo" and self.source_mode != "synthetic_demo":
            raise ValueError("demo requires SOURCE_MODE=synthetic_demo")
        if self.app_env == "production" and self.source_mode != "dataset":
            raise ValueError("production requires SOURCE_MODE=dataset")
        if self.source_mode == "official_discord":
            raise ValueError("official_discord is intentionally out of scope")
        if self.llm_temperature != 0:
            raise ValueError("LLM_TEMPERATURE must be 0")
        if self.llm_batch_size < 1 or self.max_concurrency < 1:
            raise ValueError("batch size and concurrency must be positive")

    @property
    def api_key_name(self) -> str:
        return {
            "gemini": "GEMINI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }.get(self.llm_provider, "")

    @property
    def api_key_configured(self) -> bool:
        return bool(self.api_key_name and os.getenv(self.api_key_name))

