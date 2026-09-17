from __future__ import annotations

import hashlib
import re


MAX_INPUT_CHARS = 4_000
PERSONAL_PATTERNS = (
    re.compile(r"\b(?:điểm\s*danh|điểm|xp)\s+(?:của\s+)?(?:tôi|mình|em)\b", re.I),
    re.compile(r"\b(?:check|xem|kiểm tra)\s+(?:xp|điểm|điểm danh)\b", re.I),
    re.compile(r"\b(?:mssv|mã sinh viên)\b", re.I),
    re.compile(r"\b\d{9,12}\b"),
    re.compile(r"\[MSSV\]", re.I),
)
INJECTION_PATTERNS = (
    re.compile(r"ignore (?:all |any )?(?:previous|prior) instructions", re.I),
    re.compile(r"bỏ qua (?:mọi |tất cả )?(?:quy định|chỉ dẫn|hướng dẫn)", re.I),
    re.compile(r"system prompt", re.I),
    re.compile(r"(?:hãy|phải) dùng deadline (?:bạn|mày) nhớ", re.I),
    re.compile(r"developer message|reveal.*prompt", re.I),
)
SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|token|secret|authorization)\s*[:=]\s*[^\s,;]+|sk-[A-Za-z0-9_-]{10,}"
)


def normalize_input(text: str) -> str:
    text = text.replace("\x00", "").strip()
    text = re.sub(r"\[@BOT\]|<@!?\d+>|@Trợ\s*lý", "", text, flags=re.I)
    return text[:MAX_INPUT_CHARS].strip()


def redact_for_model(text: str) -> str:
    text = normalize_input(text)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)
    text = re.sub(r"\b\d{9,12}\b", "[REDACTED_ID]", text)
    text = re.sub(r"\[(?:MSSV|EMAIL|PHONE|ID|PASSCODE)\]", "[REDACTED_PERSONAL]", text, flags=re.I)
    return text


def detect_personal_request(text: str) -> bool:
    return any(pattern.search(text) for pattern in PERSONAL_PATTERNS)


def detect_prompt_injection(text: str) -> bool:
    return any(pattern.search(text) for pattern in INJECTION_PATTERNS)


def sanitize_exception(exc: BaseException) -> str:
    message = SECRET_PATTERN.sub("[REDACTED]", str(exc))
    message = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]", message)
    message = re.sub(r"\b\d{9,12}\b", "[ID]", message)
    return message[:500]


def safe_question_ref(msg_id: str, content: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
    return f"{msg_id}:{digest}"


def escape_mentions(text: str) -> str:
    return text.replace("@", "@\u200b")
