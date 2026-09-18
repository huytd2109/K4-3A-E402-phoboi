from __future__ import annotations

from datetime import timezone, timedelta

from phoboi.handoff import HandoffRegistry
from phoboi.models import Analysis, Decision, Intent, OfficialSource, Outcome
from phoboi.resolver import resolve_sources
from phoboi.security import escape_mentions
from phoboi.sources import SourceStore

UTC_PLUS_7 = timezone(timedelta(hours=7))


def _handoff_decision(analysis: Analysis, content: str, registry: HandoffRegistry, outcome: Outcome, response: str, sources: list[OfficialSource]) -> Decision:
    ids = [source.source_id for source in sources]
    return Decision(
        msg_id=analysis.msg_id,
        intents=analysis.intents,
        outcome=outcome,
        response=response,
        prompt_injection_detected=analysis.prompt_injection_detected,
        source_ids=ids,
        handoff=registry.create(analysis, content, outcome.value, ids),
        learning_route="Chuyển câu hỏi học tập sang kênh hỗ trợ bài học." if Intent.LEARNING in analysis.intents else None,
    )


def _format_verified(source: OfficialSource) -> tuple[str, list[str]]:
    url = source.provenance_url
    if not url:
        raise ValueError("verified source has no resolvable provenance")
    if source.logistics_type == "deadline" and source.deadline:
        shown = source.deadline.astimezone(UTC_PLUS_7).strftime("%H:%M, %d/%m/%Y")
        response = f"Hạn nộp {escape_mentions(source.task_id)}: **{shown} (UTC+7)**. Nguồn: {url}"
        if source.submission_url:
            response += f". Nộp bài: {source.submission_url}"
    elif source.submission_url:
        response = f"Thông tin nộp {escape_mentions(source.task_id)}: {source.submission_url}. Nguồn: {url}"
    else:
        response = f"Đã xác minh thông tin {escape_mentions(source.task_id)}. Nguồn: {url}"
    return response, [url]


def decide(analysis: Analysis, content: str, store: SourceStore, registry: HandoffRegistry | None = None) -> Decision:
    registry = registry or HandoffRegistry()
    injection = analysis.prompt_injection_detected
    if analysis.personal_data_request or Intent.PERSONAL_RESTRICTED in analysis.intents:
        return Decision(
            msg_id=analysis.msg_id,
            intents=analysis.intents,
            outcome=Outcome.RESTRICT_PERSONAL,
            response="Mình không có quyền xem dữ liệu điểm danh, XP hoặc điểm số cá nhân. Đừng gửi MSSV công khai; hãy dùng ticket hỗ trợ riêng.",
            prompt_injection_detected=injection,
        )

    logistics = [intent for intent in analysis.intents if intent.value.startswith("LOGISTICS_")]
    if not logistics:
        if Intent.GREETING in analysis.intents and len(analysis.intents) == 1:
            return Decision(msg_id=analysis.msg_id, intents=analysis.intents, outcome=Outcome.ANSWER_GREETING, response="Chào bạn! Mình có thể giúp kiểm tra logistics từ nguồn chính thức.", prompt_injection_detected=injection)
        if Intent.LEARNING in analysis.intents:
            return Decision(msg_id=analysis.msg_id, intents=analysis.intents, outcome=Outcome.ROUTE_LEARNING, response="Mình đã chuyển phần câu hỏi học tập sang luồng hỗ trợ bài học.", prompt_injection_detected=injection, learning_route="Kênh hỗ trợ bài học")
        return Decision(msg_id=analysis.msg_id, intents=analysis.intents, outcome=Outcome.OUT_OF_SCOPE, response="Câu hỏi này nằm ngoài phạm vi logistics mà mình hỗ trợ.", prompt_injection_detected=injection)

    if analysis.confidence < 0.55:
        return _handoff_decision(analysis, content, registry, Outcome.HANDOFF_LOW_CONFIDENCE, "Mình chưa đủ chắc về ý định của câu hỏi nên cần TA kiểm tra, không tự suy đoán.", [])
    if not analysis.entities.task:
        return Decision(
            msg_id=analysis.msg_id,
            intents=analysis.intents,
            outcome=Outcome.CLARIFY,
            response="Bạn đang hỏi nhiệm vụ hoặc Lab nào?",
            prompt_injection_detected=injection,
            learning_route="Kênh hỗ trợ bài học" if Intent.LEARNING in analysis.intents else None,
        )

    sources = store.search(analysis)
    resolution = resolve_sources(sources, cohort=analysis.entities.cohort, class_scope=analysis.entities.class_scope)
    if resolution.kind == "clarify":
        question = "Bạn thuộc cohort nào?" if resolution.missing_field == "cohort" else "Bạn thuộc lớp nào?"
        return Decision(msg_id=analysis.msg_id, intents=analysis.intents, outcome=Outcome.CLARIFY, response=question, prompt_injection_detected=injection)
    if resolution.kind == "no_source":
        return _handoff_decision(analysis, content, registry, Outcome.HANDOFF_NO_SOURCE, "Mình chưa tìm được thông tin trong nguồn chính thức nên sẽ không đoán. Bạn cần nhờ TA xác nhận thông tin này.", [])
    if resolution.kind == "conflict":
        return _handoff_decision(analysis, content, registry, Outcome.HANDOFF_CONFLICT, "Mình tìm thấy các nguồn chính thức có thông tin khác nhau và không có quan hệ thay thế rõ ràng. Cần TA kiểm tra thông tin này.", resolution.sources)

    selected = resolution.sources[0]
    if store.mode != "synthetic_demo" or not selected.is_fixture or selected.source_type != "synthetic_demo":
        return _handoff_decision(analysis, content, registry, Outcome.HANDOFF_NO_SOURCE, "Nguồn tìm thấy chỉ là UNVERIFIED CANDIDATE nên mình không trả deadline. Cần TA xác nhận thông tin này.", [])
    response, urls = _format_verified(selected)
    return Decision(
        msg_id=analysis.msg_id,
        intents=analysis.intents,
        outcome=Outcome.ANSWER_VERIFIED,
        response=response,
        prompt_injection_detected=injection,
        source_ids=[source.source_id for source in resolution.sources],
        source_urls=urls,
        badge="DỮ LIỆU DEMO",
        learning_route="Chuyển phần học tập sang kênh hỗ trợ bài học." if Intent.LEARNING in analysis.intents else None,
    )
