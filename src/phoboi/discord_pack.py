"""Local, non-authoritative retrieval over the anonymized Discord data pack."""

from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


_STOPWORDS = {
    "a",
    "ai",
    "anh",
    "ban",
    "biet",
    "cho",
    "co",
    "cua",
    "da",
    "de",
    "duoc",
    "em",
    "gi",
    "giup",
    "hay",
    "la",
    "minh",
    "mot",
    "nay",
    "nhe",
    "oi",
    "the",
    "thi",
    "toi",
    "va",
    "voi",
}

_DOMAIN_TOKENS = {
    "codelab",
    "daily",
    "deadline",
    "diem",
    "danh",
    "lab",
    "link",
    "nop",
    "standup",
    "team",
    "workshop",
    "xp",
}


@dataclass(frozen=True)
class DiscordMessage:
    msg_id: str
    guild: str
    channel: str
    author: str
    is_bot: bool
    created_at_vn: str
    content: str
    tokens: frozenset[str]


@dataclass(frozen=True)
class DiscordPackMatch:
    """Safe retrieval result; raw peer content is intentionally excluded."""

    msg_id: str
    guild: str
    channel: str
    created_at_vn: str
    is_bot: bool
    score: float


class DiscordPackRepository:
    """Search anonymized history without treating it as an official source."""

    def __init__(self) -> None:
        self._messages: list[DiscordMessage] = []

    def load_from_csv(self, path: str | Path) -> None:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Discord data pack not found: {file_path}")

        messages: list[DiscordMessage] = []
        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                content = row.get("content", "")
                msg_id = row.get("msg_id", "").strip()
                if not msg_id or not content.strip():
                    continue
                messages.append(
                    DiscordMessage(
                        msg_id=msg_id,
                        guild=row.get("guild", "").strip(),
                        channel=row.get("channel", "").strip(),
                        author=row.get("author", "").strip(),
                        is_bot=row.get("is_bot", "").strip().lower() == "true",
                        created_at_vn=row.get("created_at_vn", "").strip(),
                        content=content,
                        tokens=frozenset(_tokens(content)),
                    )
                )
        self._messages = messages

    def search(self, query: str, *, limit: int = 5) -> list[DiscordPackMatch]:
        query_tokens = _tokens(query)
        if not query_tokens or limit <= 0:
            return []

        ranked: list[tuple[float, DiscordMessage]] = []
        for message in self._messages:
            overlap = query_tokens & message.tokens
            if len(overlap) < 2:
                continue
            score = float(len(overlap))
            score += sum(1.5 for token in overlap if token in _DOMAIN_TOKENS)
            if not message.is_bot:
                score += 0.1
            ranked.append((score, message))

        ranked.sort(key=lambda item: (-item[0], item[1].msg_id))
        return [
            DiscordPackMatch(
                msg_id=message.msg_id,
                guild=message.guild,
                channel=message.channel,
                created_at_vn=message.created_at_vn,
                is_bot=message.is_bot,
                score=score,
            )
            for score, message in ranked[:limit]
        ]

    @property
    def count(self) -> int:
        return len(self._messages)


def _tokens(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFD", text.lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = normalized.replace("đ", "d")
    normalized = re.sub(r"([a-z])([0-9])", r"\1 \2", normalized)
    normalized = re.sub(r"([0-9])([a-z])", r"\1 \2", normalized)
    values = re.findall(r"[a-z0-9]+", normalized)
    return {value for value in values if len(value) > 1 and value not in _STOPWORDS}
