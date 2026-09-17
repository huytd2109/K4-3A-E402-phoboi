from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path

from phoboi.models import DatasetMessage

REQUIRED_COLUMNS = {
    "msg_id", "guild", "channel", "author", "is_bot", "msg_type", "created_at_vn",
    "reply_to", "mentions_bot", "n_attachments", "n_chars", "content",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_bool(value: str) -> bool:
    if value not in {"True", "False"}:
        raise ValueError(f"invalid boolean value: {value!r}")
    return value == "True"


def load_messages(path: Path) -> list[DatasetMessage]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if set(reader.fieldnames or []) != REQUIRED_COLUMNS:
            missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
            extra = set(reader.fieldnames or []) - REQUIRED_COLUMNS
            raise ValueError(f"dataset schema mismatch; missing={sorted(missing)}, extra={sorted(extra)}")
        rows = []
        seen_counts: dict[str, int] = {}
        for line_number, raw in enumerate(reader, 2):
            msg_id = raw["msg_id"]
            if not re.fullmatch(r"M\d{5}", msg_id):
                raise ValueError(f"invalid msg_id at line {line_number}")
            occurrence = seen_counts.get(msg_id, 0) + 1
            seen_counts[msg_id] = occurrence
            record_id = msg_id if occurrence == 1 else f"{msg_id}#{occurrence}"
            rows.append(DatasetMessage(
                record_id=record_id,
                msg_id=msg_id,
                guild=raw["guild"],
                channel=raw["channel"],
                author=raw["author"],
                is_bot=_as_bool(raw["is_bot"]),
                msg_type=raw["msg_type"],
                created_at_vn=raw["created_at_vn"],
                reply_to=raw["reply_to"] or None,
                mentions_bot=_as_bool(raw["mentions_bot"]),
                n_attachments=int(raw["n_attachments"]),
                n_chars=int(raw["n_chars"]),
                content=raw["content"],
            ))
    return rows


def baseline_characteristics(content: str) -> dict[str, object]:
    lowered = content.casefold()
    return {
        "n_chars": len(content),
        "has_source_link": "[link:" in lowered or "http" in lowered,
        "mentions_time_or_deadline": bool(re.search(r"deadline|hạn|\b\d{1,2}:\d{2}\b", lowered)),
        "has_uncertainty_or_handoff": any(word in lowered for word in ("không chắc", "chưa xác nhận", "ticket", "liên hệ", "hỗ trợ")),
    }
