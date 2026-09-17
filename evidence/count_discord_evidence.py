"""Reproduce the CP4 evidence counts from the anonymized Discord pack.

Run from the repository root:
    python evidence/count_discord_evidence.py

The three candidate groups are intentionally independent. A mixed question may
appear in more than one group. This script prints identifiers, never unmasks or
infers a real person's identity.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path


DATA_PATH = Path("data/discord-pack/k4_messages.csv")

QUESTION_SIGNAL = re.compile(
    r"\?|bao giờ|khi nào|mấy giờ|ở đâu|như thế nào|thế nào|sao "
    r"|được không|cho (?:em|mình|tôi) hỏi|xin",
    re.IGNORECASE,
)

CANDIDATES = {
    "deadline_submission": re.compile(
        r"deadline|hạn nộp|hạn chót|hết hạn|gia hạn|nộp muộn|trễ hạn"
        r"|ghép đội|lập đội|thành lập (?:team|đội)|link nộp"
        r"|nộp (?:bài|lab|codelab)|submit|submission|nộp ở đâu"
        r"|commit.*deadline",
        re.IGNORECASE,
    ),
    "personal_attendance_xp": re.compile(
        r"điểm danh|\bxp\b|bảng điểm|lịch sử điểm danh",
        re.IGNORECASE,
    ),
    "resource_retrieval": re.compile(
        r"\brecord(?:ing)?\b|xin (?:.* )?slide|xin (?:.* )?sổ tay"
        r"|lấy slide|slide.*ở đâu|tài liệu học.*ở đâu",
        re.IGNORECASE,
    ),
}


def truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def main() -> None:
    with DATA_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    human_rows = [row for row in rows if not truthy(row["is_bot"])]
    print(f"all_messages={len(rows)}")
    print(f"human_messages={len(human_rows)}")
    print(f"bot_messages={len(rows) - len(human_rows)}")

    for name, pattern in CANDIDATES.items():
        matches = [
            row
            for row in human_rows
            if pattern.search(row["content"])
            and QUESTION_SIGNAL.search(row["content"])
        ]
        authors = {row["author"] for row in matches}
        bot_mentions = sum(truthy(row["mentions_bot"]) for row in matches)
        message_ids = ", ".join(row["msg_id"] for row in matches)
        print(
            f"{name}: messages={len(matches)}, authors={len(authors)}, "
            f"bot_mentions={bot_mentions}"
        )
        print(f"  msg_ids={message_ids}")


if __name__ == "__main__":
    main()
