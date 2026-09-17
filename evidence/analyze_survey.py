"""Reproduce the CP4 survey metrics without changing the raw CSV.

Run from the repository root:
    python evidence/analyze_survey.py
"""

from __future__ import annotations

import csv
from pathlib import Path


SURVEY_PATH = Path("evidence/survey.csv")


def percentage(count: int, total: int) -> str:
    return f"{count / total * 100:.1f}%"


def main() -> None:
    with SURVEY_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        raise SystemExit("survey.csv has no responses")

    columns = list(rows[0])
    by_question = {
        int(column.split(".", 1)[0].removeprefix("Câu ")): column
        for column in columns
        if column.startswith("Câu ")
    }
    total = len(rows)

    q1_at_least_once = sum(bool(row[by_question[1]].strip()) for row in rows)
    q1_at_least_three = sum(
        row[by_question[1]].strip() in {"3–5 lần", "6–10 lần", "Trên 10 lần"}
        for row in rows
    )
    q4_at_least_five_minutes = sum(
        row[by_question[4]].strip() in {"5–10 phút", "10–20 phút", "Trên 20 phút"}
        for row in rows
    )
    q5_multiple_sources = sum(
        row[by_question[5]].strip().startswith("Có,") for row in rows
    )
    q8_asked_again = sum(
        row[by_question[8]].strip() != "Chưa từng" for row in rows
    )

    q9_values = [row[by_question[9]].strip() for row in rows]
    q9_clean_consequence = sum(
        bool(value) and "Chưa từng gặp vấn đề" not in value for value in q9_values
    )
    q9_contradictory = sum(
        "Chưa từng gặp vấn đề" in value
        and value != "Chưa từng gặp vấn đề"
        for value in q9_values
    )

    trusted_official = {
        "Có xác nhận của TA / BTC",
        "Có trích đoạn từ nguồn chính thức",
        "Có link dẫn tới nguồn chính thức",
    }
    q10_official_or_ta = sum(
        row[by_question[10]].strip() in trusted_official for row in rows
    )
    safe_failure = {
        "Báo rằng chưa chắc chắn và chuyển câu hỏi cho TA",
        "Hỏi thêm thông tin để làm rõ câu hỏi",
    }
    q11_handoff_or_clarify = sum(
        row[by_question[11]].strip() in safe_failure for row in rows
    )

    q7_nonempty = sum(bool(row[by_question[7]].strip()) for row in rows)
    q12_nonempty = sum(bool(row[by_question[12]].strip()) for row in rows)

    metrics = [
        ("Responses", total),
        ("Needed logistics information at least once in 7 days", q1_at_least_once),
        ("Needed it at least 3 times in 7 days", q1_at_least_three),
        ("Spent at least 5 minutes", q4_at_least_five_minutes),
        ("Checked at least 2 sources", q5_multiple_sources),
        ("Asked TA or a peer at least once", q8_asked_again),
        ("Reported a clean, non-contradictory consequence", q9_clean_consequence),
        ("Trust an official source or TA/BTC confirmation", q10_official_or_ta),
        ("Prefer handoff or clarification when no source", q11_handoff_or_clarify),
        ("Q7 non-empty open responses", q7_nonempty),
        ("Q12 non-empty open responses", q12_nonempty),
        ("Contradictory Q9 checkbox responses", q9_contradictory),
    ]

    for label, count in metrics:
        if label == "Responses":
            print(f"{label}: {count}")
        else:
            print(f"{label}: {count}/{total} ({percentage(count, total)})")


if __name__ == "__main__":
    main()
