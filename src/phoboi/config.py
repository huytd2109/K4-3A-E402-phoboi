"""Centralized configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file if present (never in tests unless explicit)
_env_path = Path.cwd() / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


class Config:
    """Application configuration — all values from env vars or defaults."""

    def __init__(self) -> None:
        self.app_env: str = os.getenv("APP_ENV", "demo").lower()

        # Source data
        self.official_sources_path: str = os.getenv(
            "OFFICIAL_SOURCES_PATH", "data/official/sources.json"
        )

        # Discord (optional — only needed for Discord adapter)
        self.discord_bot_token: str = os.getenv("DISCORD_BOT_TOKEN", "")
        self.discord_guild_id: str = os.getenv("DISCORD_GUILD_ID", "")
        self.discord_ta_role_id: str = os.getenv("DISCORD_TA_ROLE_ID", "")
        self.discord_handoff_channel_id: str = os.getenv("DISCORD_HANDOFF_CHANNEL_ID", "")

        # Authorized sources
        raw_channels = os.getenv("AUTHORIZED_CHANNEL_IDS", "")
        self.authorized_channel_ids: list[str] = [
            c.strip() for c in raw_channels.split(",") if c.strip()
        ]
        raw_roles = os.getenv("AUTHORIZED_ROLE_IDS", "")
        self.authorized_role_ids: list[str] = [
            r.strip() for r in raw_roles.split(",") if r.strip()
        ]

        # Support
        self.support_route: str = os.getenv("SUPPORT_ROUTE", "#hỗ-trợ-riêng")

        # Safety limits
        self.max_input_length: int = int(os.getenv("MAX_INPUT_LENGTH", "2000"))
        self.handoff_cooldown_seconds: int = int(
            os.getenv("HANDOFF_COOLDOWN_SECONDS", "300")
        )

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"

    @property
    def is_demo(self) -> bool:
        return self.app_env == "demo"

    @property
    def allows_fixtures(self) -> bool:
        """Fixture data is only permitted in test/demo mode."""
        return self.app_env in ("test", "demo")


# Singleton for convenience; tests should create their own Config instances
_config: Config | None = None


def get_config() -> Config:
    """Get or create the global config singleton."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reset_config() -> None:
    """Reset the global config (for tests)."""
    global _config
    _config = None

