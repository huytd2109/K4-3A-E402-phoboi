"""Multi-label intent router.

Rule-based classifier for deterministic, offline operation.
Designed with a provider interface so an LLM-based classifier
can be swapped in later without changing the pipeline contract.
"""

from __future__ import annotations

import re
from typing import Protocol

from phoboi.models import ExtractionResult, Intent, LogisticsType, RouterResult


# ── Provider interface ────────────────────────────────────────────


class IntentRouterProvider(Protocol):
    """Interface for intent classification providers."""

    def classify(self, text: str) -> RouterResult: ...


# ── Keyword patterns ─────────────────────────────────────────────

# Vietnamese + English patterns for each intent category

_GREETING_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"^(xin\s+)?chào(\s+mọi\s+người)?[.!?\s]*$",
        r"^(hi|hello|hey|yo)\b[.!?\s]*$",
        r"^chào\s+(buổi\s+)?(sáng|chiều|tối)[.!?\s]*$",
        r"^(good\s+)?(morning|afternoon|evening)[.!?\s]*$",
        r"^ê+[.!?\s]*$",
        r"^mọi\s+người\s+ơi[.!?\s]*$",
    ]
]

_DEADLINE_KEYWORDS: list[str] = [
    "deadline", "hạn nộp", "hạn chót", "khi nào", "bao giờ",
    "thời hạn", "due date", "due", "hết hạn", "đến hạn",
    "trước khi nào", "nộp trước", "nộp muộn",
    "thời gian nộp", "ngày nộp", "trước ngày nào",
    "nộp lúc nào", "nộp bao giờ",
]

_LINK_KEYWORDS: list[str] = [
    "link nộp", "link bài", "nộp ở đâu", "nộp bài ở đâu",
    "url", "đường link", "trang nộp", "vlearn",
    "nộp trên", "link submit",
]

_SUBMISSION_KEYWORDS: list[str] = [
    "cách nộp", "nộp như thế nào", "nộp bằng cách nào",
    "hướng dẫn nộp", "quy trình nộp", "submit how",
    "format nộp", "yêu cầu nộp", "nộp ở đâu",
]

_PERSONAL_KEYWORDS: list[str] = [
    "điểm danh", "xp của", "điểm của", "điểm số",
    "lịch sử điểm", "attendance", "my score", "my xp",
    "mssv", "tài khoản", "account",
    "điểm danh của tôi", "điểm danh của em", "điểm danh của mình",
    "xp của tôi", "xp của em", "xp của mình",
    "bảng điểm", "kết quả", "điểm thi",
]

_LEARNING_KEYWORDS: list[str] = [
    "cài đặt", "install", "setup", "lỗi code", "code lỗi",
    "error", "bug", "debug", "tutorial",
    "bài học", "lesson", "exercise", "làm sao để",
    "giải thích", "explain", "tại sao", "khó quá",
    "không hiểu",
    "chạy code", "run code", "docker",
    "python", "github", "branch", "commit",
    "cvat", "annotation", "train model", "train", "resnet",
]

# Task name patterns for extraction
_TASK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(?:lab|bài\s*lab)\s*0*(\d+)\b", re.IGNORECASE), "lab-{:02d}"),
    (re.compile(r"\b(?:workshop|ws)\s*0*(\d+)\b", re.IGNORECASE), "workshop-{:02d}"),
    (re.compile(r"\b(?:codelab)\s*0*(\d+)\b", re.IGNORECASE), "codelab-{:02d}"),
    (re.compile(r"\b(?:daily\s*standup|standup|daily)\b", re.IGNORECASE), "daily-standup"),
    (re.compile(r"\b(?:team|nhóm|đội)\b.*?(?:formation|thành\s*lập|lập|ghép)", re.IGNORECASE), "team-formation"),
    (re.compile(r"\b(?:ghép\s*(?:đội|nhóm))\b", re.IGNORECASE), "team-formation"),
    (re.compile(r"\b(?:lập\s*(?:đội|nhóm))\b", re.IGNORECASE), "team-formation"),
    (re.compile(r"\b(?:thành\s*lập\s*(?:đội|nhóm|team))\b", re.IGNORECASE), "team-formation"),
    (re.compile(r"\b(?:chốt\s*team)\b", re.IGNORECASE), "team-formation"),
    (re.compile(r"\b(?:đăng\s*ký\s*nhóm)\b", re.IGNORECASE), "team-formation"),
]

_COHORT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bK4\b", re.IGNORECASE), "K4"),
    (re.compile(r"\bkhoá\s*4\b", re.IGNORECASE), "K4"),
    (re.compile(r"\bcohort\s*4\b", re.IGNORECASE), "K4"),
]

_CLASS_SCOPE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bL2[-–]3\b", re.IGNORECASE), "L2-3"),
    (re.compile(r"\bL3[-–]4\b", re.IGNORECASE), "L3-4"),
    (re.compile(r"\blevel\s*2\b", re.IGNORECASE), "L2-3"),
    (re.compile(r"\blevel\s*3\b", re.IGNORECASE), "L3-4"),
]


# ── Rule-based router ────────────────────────────────────────────


class RuleBasedRouter(IntentRouterProvider):
    """Deterministic, keyword/pattern-based multi-label intent router.

    Runs offline without any API calls. Suitable for demo and as a
    fallback when LLM is unavailable.
    """

    def classify(self, text: str) -> RouterResult:
        text_lower = text.lower().strip()
        intents: list[Intent] = []

        # Check greeting (only if it's the entire message)
        for pat in _GREETING_PATTERNS:
            if pat.match(text_lower):
                intents.append(Intent.GREETING)
                break

        # Check personal/restricted
        if self._matches_any(text_lower, _PERSONAL_KEYWORDS):
            intents.append(Intent.PERSONAL_RESTRICTED)

        # Check logistics subtypes
        has_deadline = self._matches_any(text_lower, _DEADLINE_KEYWORDS)
        has_link = self._matches_any(text_lower, _LINK_KEYWORDS)
        has_submission = self._matches_any(text_lower, _SUBMISSION_KEYWORDS)

        if has_deadline:
            intents.append(Intent.LOGISTICS_DEADLINE)
        if has_link:
            intents.append(Intent.LOGISTICS_LINK)
        if has_submission:
            intents.append(Intent.LOGISTICS_SUBMISSION)

        # Check learning
        if self._matches_any(text_lower, _LEARNING_KEYWORDS):
            # Only add LEARNING if the message isn't purely logistics
            # (lab/codelab can be both learning and logistics context)
            if not (has_deadline or has_link or has_submission):
                intents.append(Intent.LEARNING)
            else:
                # Mixed: both learning and logistics
                intents.append(Intent.LEARNING)

        # If nothing matched
        if not intents:
            # Check if it looks like a question at all
            if "?" in text or any(
                q in text_lower
                for q in ["gì", "nào", "sao", "đâu", "không", "bao giờ", "ai"]
            ):
                intents.append(Intent.UNKNOWN)
            else:
                intents.append(Intent.OUT_OF_SCOPE)

        # Extract entities
        extraction = self._extract_entities(text, text_lower, intents)

        return RouterResult(
            intents=intents,
            confidence=1.0,  # Rule-based is deterministic
            extraction=extraction,
        )

    def _matches_any(self, text: str, keywords: list[str]) -> bool:
        return any(kw in text for kw in keywords)

    def _extract_entities(
        self, text: str, text_lower: str, intents: list[Intent]
    ) -> ExtractionResult:
        task: str | None = None
        task_normalized: str | None = None
        cohort: str | None = None
        class_scope: str | None = None
        logistics_type: LogisticsType | None = None

        # Extract task
        for pattern, fmt in _TASK_PATTERNS:
            match = pattern.search(text)
            if match:
                task = match.group(0)
                if "{" in fmt:
                    task_normalized = fmt.format(int(match.group(1)))
                else:
                    task_normalized = fmt
                break

        # Extract cohort
        for pattern, cohort_val in _COHORT_PATTERNS:
            if pattern.search(text):
                cohort = cohort_val
                break

        # Extract class scope
        for pattern, scope_val in _CLASS_SCOPE_PATTERNS:
            if pattern.search(text):
                class_scope = scope_val
                break

        # Determine logistics type
        logistics_intents = [
            i for i in intents
            if i in (
                Intent.LOGISTICS_DEADLINE,
                Intent.LOGISTICS_LINK,
                Intent.LOGISTICS_SUBMISSION,
            )
        ]
        if logistics_intents:
            # Use the first logistics intent as the type
            lt_map = {
                Intent.LOGISTICS_DEADLINE: LogisticsType.DEADLINE,
                Intent.LOGISTICS_LINK: LogisticsType.LINK,
                Intent.LOGISTICS_SUBMISSION: LogisticsType.SUBMISSION,
            }
            logistics_type = lt_map.get(logistics_intents[0])

        return ExtractionResult(
            task=task,
            task_normalized=task_normalized,
            cohort=cohort,
            class_scope=class_scope,
            logistics_type=logistics_type,
        )


# ── Factory ──────────────────────────────────────────────────────


def create_router(provider: str = "rule_based") -> IntentRouterProvider:
    """Create an intent router. Only rule_based is available in MVP."""
    if provider == "rule_based":
        return RuleBasedRouter()
    raise ValueError(f"Unknown router provider: {provider}")
