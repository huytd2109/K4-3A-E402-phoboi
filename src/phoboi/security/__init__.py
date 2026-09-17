"""Input sanitization, prompt injection detection, and output escaping.

Trust boundary: Discord messages are UNTRUSTED input.
This module ensures no injection, mention abuse, or data leak.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ── Patterns ──────────────────────────────────────────────────────

# Bot mention patterns (Discord format or known display names). Keep email
# addresses and arbitrary mentions intact so PII detection can still see them.
_BOT_MENTION_RE = re.compile(
    r"<@!?\d+>|@(?:bot|trợ-lý|tro-ly)\b",
    re.IGNORECASE,
)

# Role and @everyone/@here mentions
_DANGEROUS_MENTION_RE = re.compile(r"@(everyone|here|&\d+)", re.IGNORECASE)

# Prompt injection patterns (case-insensitive)
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"(bỏ qua|ignore|disregard|forget).{0,30}(quy định|rules?|instructions?|policy|system)",
        r"system\s*prompt",
        r"(hãy|please).{0,20}(dùng|use).{0,20}(deadline|thời hạn).{0,20}(bạn|you).{0,20}(nhớ|remember|know)",
        r"(pretend|giả vờ|act as|đóng vai)",
        r"(reveal|show|hiện|cho xem).{0,20}(system|hệ thống|prompt|config)",
        r"(override|ghi đè|thay đổi).{0,20}(policy|chính sách|rules?|quy tắc)",
        r"\[INST\]|\[/INST\]|<\|im_start\|>|<\|im_end\|>",
        r"(new|begin|start)\s*(instruction|system|conversation)",
        r"(DAN|developer mode|jailbreak)",
    ]
]

# Markdown/URL that could be abusive
_SUSPICIOUS_URL_RE = re.compile(r"https?://\S{500,}", re.IGNORECASE)

# MSSV, email, phone patterns for PII detection
_PII_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b\d{10,13}\b"),  # MSSV-like
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    re.compile(r"\b0\d{9,10}\b"),  # Phone
]


# ── Result ────────────────────────────────────────────────────────


@dataclass
class SanitizeResult:
    """Result of sanitizing a user message."""

    cleaned: str
    raw_hash: str = ""
    is_injection_attempt: bool = False
    injection_patterns_matched: list[str] = field(default_factory=list)
    was_truncated: bool = False
    mentions_removed: list[str] = field(default_factory=list)
    contains_pii: bool = False


# ── Public API ────────────────────────────────────────────────────


def sanitize_input(
    raw_message: str,
    *,
    max_length: int = 2000,
) -> SanitizeResult:
    """Sanitize a raw user message for pipeline processing.

    1. Truncate to max_length
    2. Strip bot mentions (not used for classification)
    3. Detect prompt injection attempts
    4. Detect PII in message
    5. Hash raw input for audit (no raw content stored)
    """
    import hashlib

    result = SanitizeResult(cleaned="")
    result.raw_hash = hashlib.sha256(raw_message.encode("utf-8")).hexdigest()

    # 1. Length limit
    if len(raw_message) > max_length:
        raw_message = raw_message[:max_length]
        result.was_truncated = True

    # 2. Strip bot mentions from content used for classification
    mentions = _BOT_MENTION_RE.findall(raw_message)
    result.mentions_removed = mentions
    cleaned = _BOT_MENTION_RE.sub("", raw_message).strip()

    # 3. Detect prompt injection
    matched_patterns: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            matched_patterns.append(match.group(0))

    if matched_patterns:
        result.is_injection_attempt = True
        result.injection_patterns_matched = matched_patterns

    # 4. PII detection
    for pii_pat in _PII_PATTERNS:
        if pii_pat.search(cleaned):
            result.contains_pii = True
            break

    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    result.cleaned = cleaned

    return result


def escape_mentions(text: str) -> str:
    """Escape Discord mentions in bot output to prevent unwanted pings.

    Prevents @everyone, @here, and role mentions from being rendered.
    """
    # Zero-width space after @ to break mention rendering
    ZWS = "\u200b"  # actual zero-width space character
    text = text.replace("@everyone", f"@{ZWS}everyone")
    text = text.replace("@here", f"@{ZWS}here")
    # Break role mentions
    text = re.sub(r"<@&(\d+)>", lambda m: f"<@{ZWS}&{m.group(1)}>", text)
    return text


def redact_pii(text: str) -> str:
    """Replace detected identifiers before text enters logs or handoff payloads."""
    redacted = text
    labels = ("[IDENTIFIER]", "[EMAIL]", "[PHONE]")
    for pattern, label in zip(_PII_PATTERNS, labels):
        redacted = pattern.sub(label, redacted)
    return redacted


def contains_system_leak_request(text: str) -> bool:
    """Check if the message is attempting to extract system information."""
    leak_patterns = [
        r"(what|show|print|display|reveal).{0,20}(system|prompt|instruction|config)",
        r"(environment|env)\s*(variable|var)",
        r"stack\s*trace",
        r"(error|exception)\s*(message|detail|log)",
        r"(cho|hiện|in ra).{0,20}(system|hệ thống|cấu hình|prompt)",
    ]
    for pattern_str in leak_patterns:
        if re.search(pattern_str, text, re.IGNORECASE):
            return True
    return False
