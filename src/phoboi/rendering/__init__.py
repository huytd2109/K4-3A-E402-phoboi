"""Template renderer — generates Vietnamese response text from PolicyDecisions.

All deadline text is populated from OfficialSource data only.
Templates are deterministic string formatting — no LLM generation.
"""

from __future__ import annotations

from datetime import timezone, timedelta
from typing import Optional

from phoboi.models import (
    LogisticsType,
    OfficialSource,
    PolicyDecision,
    PolicyOutcome,
)

# UTC+7 timezone
UTC_PLUS_7 = timezone(timedelta(hours=7))


def render_response(
    decisions: list[PolicyDecision],
    *,
    support_route: str = "#hỗ-trợ-riêng",
    is_fixture: bool = False,
) -> str:
    """Render a complete response from one or more policy decisions.

    For multi-intent messages, each decision is rendered as a separate section.
    """
    parts: list[str] = []

    for decision in decisions:
        rendered = _render_single(decision, support_route=support_route)
        if rendered:
            parts.append(rendered)

    if not parts:
        parts.append("Mình không hiểu câu hỏi. Bạn có thể diễn đạt lại được không?")

    response = "\n\n".join(parts)

    # Add fixture banner if applicable
    if is_fixture:
        response = "⚠️ *[Demo — dữ liệu mẫu, không phải deadline thật]*\n\n" + response

    return response


def _render_single(
    decision: PolicyDecision,
    *,
    support_route: str = "#hỗ-trợ-riêng",
) -> str:
    """Render a single policy decision."""

    match decision.outcome:
        case PolicyOutcome.ANSWER_VERIFIED:
            return _render_verified(decision)

        case PolicyOutcome.ANSWER_GREETING:
            return "Chào bạn! Mình có thể giúp gì về deadline, link nộp bài hoặc cách nộp? 😊"

        case PolicyOutcome.CLARIFY:
            return _render_clarify(decision)

        case PolicyOutcome.HANDOFF_NO_SOURCE:
            return (
                "Mình chưa tìm được thông tin này trong nguồn chính thức nên sẽ không đoán. "
                "Mình đã chuyển câu hỏi này cho TA."
            )

        case PolicyOutcome.HANDOFF_CONFLICT:
            return (
                "Mình tìm thấy hai thông báo chính thức có thông tin khác nhau "
                "và chưa xác định được thông báo nào thay thế. "
                "Mình đã chuyển TA kiểm tra."
            )

        case PolicyOutcome.HANDOFF_LOW_CONFIDENCE:
            return (
                "Mình không chắc mình hiểu đúng câu hỏi. "
                "Mình đã chuyển cho TA để hỗ trợ bạn."
            )

        case PolicyOutcome.RESTRICT_PERSONAL:
            return (
                "Mình không có quyền xem thông tin cá nhân (điểm danh, XP, điểm số). "
                "Bạn không nên gửi MSSV tại kênh công khai; "
                f"hãy dùng kênh hỗ trợ riêng: {support_route}."
            )

        case PolicyOutcome.ROUTE_LEARNING:
            return (
                "Câu hỏi này về nội dung bài học — mình tập trung hỗ trợ logistics "
                "(deadline, link, cách nộp). Bạn có thể hỏi TA hoặc bạn học để được giải đáp chi tiết hơn."
            )

        case PolicyOutcome.OUT_OF_SCOPE:
            return (
                "Câu hỏi này nằm ngoài phạm vi hỗ trợ của mình. "
                "Mình có thể giúp về deadline, link nộp bài hoặc cách nộp."
            )

    return ""


def _render_verified(decision: PolicyDecision) -> str:
    """Render a verified answer with source citation."""
    source = decision.source
    assert source is not None, "ANSWER_VERIFIED must have a source"
    assert source.source_url, "ANSWER_VERIFIED source must have a URL"

    lines: list[str] = []

    # Main answer based on logistics type
    if source.logistics_type == LogisticsType.DEADLINE and source.deadline:
        deadline_vn = source.deadline.astimezone(UTC_PLUS_7)
        formatted = deadline_vn.strftime("%H:%M, %d/%m/%Y")
        task_display = _task_display_name(source.task_id)
        lines.append(f"Hạn nộp {task_display}: **{formatted} (UTC+7)**.")

    elif source.logistics_type == LogisticsType.LINK:
        task_display = _task_display_name(source.task_id)
        if source.submission_url:
            lines.append(f"Link cho {task_display}: {source.submission_url}")
        else:
            lines.append(f"Thông tin về {task_display} — xem chi tiết tại nguồn bên dưới.")

    elif source.logistics_type == LogisticsType.SUBMISSION:
        task_display = _task_display_name(source.task_id)
        lines.append(f"Thông tin cách nộp {task_display} — xem chi tiết tại nguồn bên dưới.")

    else:
        task_display = _task_display_name(source.task_id)
        if source.deadline:
            deadline_vn = source.deadline.astimezone(UTC_PLUS_7)
            formatted = deadline_vn.strftime("%H:%M, %d/%m/%Y")
            lines.append(f"Hạn nộp {task_display}: **{formatted} (UTC+7)**.")
        else:
            lines.append(f"Thông tin về {task_display} — xem chi tiết tại nguồn bên dưới.")

    # Source citation
    lines.append(f"Nguồn chính thức: [Thông báo]({source.source_url}).")

    # Submission URL if available and not already shown
    if source.submission_url and source.logistics_type != LogisticsType.LINK:
        lines.append(f"Nộp bài: {source.submission_url}")

    return "\n".join(lines)


def _render_clarify(decision: PolicyDecision) -> str:
    """Render a clarification request."""
    if decision.missing_fields:
        field_desc = ", ".join(decision.missing_fields)
        return f"Mình cần thêm thông tin để trả lời chính xác: {field_desc}. Bạn có thể cho mình biết thêm không?"
    return "Bạn có thể cho mình thêm chi tiết không?"


def _task_display_name(task_id: str) -> str:
    """Convert task_id to display name."""
    parts = task_id.split("-")
    if len(parts) == 2:
        prefix = parts[0].capitalize()
        try:
            num = int(parts[1])
            return f"{prefix} {num}"
        except ValueError:
            return task_id.replace("-", " ").title()
    return task_id.replace("-", " ").title()

