from __future__ import annotations


RATE_LIMIT_MESSAGE = (
    "Trợ lý hơi đuối rồi 😴 Cho mình nghỉ lấy sức nhé, bạn thử lại sau nha!"
)


def is_rate_limit_error(exc: BaseException) -> bool:
    """Recognize SDK HTTP 429 errors, including wrapped provider failures."""
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        response = getattr(current, "response", None)
        statuses = (
            getattr(current, "status_code", None),
            getattr(current, "code", None),
            getattr(response, "status_code", None),
        )
        if any(str(status) == "429" for status in statuses):
            return True
        current = current.__cause__ or current.__context__
    return False
