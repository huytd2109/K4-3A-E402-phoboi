"""Bounded, process-local context for chat; never a source of official facts."""
from __future__ import annotations

import json
import re
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from threading import Lock

from phoboi.models import Analysis, Decision, Outcome
from phoboi.security import redact_for_model


@dataclass
class Conversation:
    turns: list[dict[str, str]] = field(default_factory=list)
    previous: Analysis | None = None
    touched: float = field(default_factory=time.monotonic)
    lock: object = field(default_factory=Lock)

    def context(self) -> str | None:
        return json.dumps(self.turns, ensure_ascii=False) if self.turns else None

    def resolve_reply(self, message: str) -> str:
        # Only an explicit standalone task inherits the previous logistics intent.
        match = re.fullmatch(r"\s*(?:còn\s+)?(lab\s*[-_#]?\s*\d+|daily\s*standup|standup)\s*[?.!]?\s*", message, re.I)
        previous = self.previous
        if not match or previous is None:
            return message
        if not any(i.value.startswith("LOGISTICS_") for i in previous.intents):
            return message
        prefix = {"deadline": "Hạn nộp", "link": "Link nộp", "submission": "Cách nộp"}.get(previous.entities.logistics_type)
        if prefix is None:
            return message
        scope = " ".join(filter(None, [previous.entities.cohort, previous.entities.class_scope]))
        return f"{prefix} {match.group(1)} {scope}?"

    def remember(self, message: str, analysis: Analysis, decision: Decision) -> None:
        self.turns.extend([
            {"role": "user", "content": redact_for_model(message)[:220]},
            {"role": "assistant", "content": redact_for_model(decision.response)[:220]},
        ])
        self.turns = self.turns[-6:]
        self.previous = analysis.model_copy(deep=True)
        if decision.outcome in {Outcome.RESTRICT_PERSONAL, Outcome.OUT_OF_SCOPE, Outcome.ROUTE_LEARNING, Outcome.ANSWER_GREETING}:
            self.previous = None
            self.turns = self.turns[-2:]
        self.touched = time.monotonic()


class ConversationStore:
    def __init__(self, max_sessions: int = 128, ttl: float = 1800):
        self.sessions: OrderedDict[str, Conversation] = OrderedDict()
        self.max_sessions = max_sessions
        self.ttl = ttl
        self.lock = Lock()

    def get(self, session_id: str | None) -> Conversation:
        if session_id is None:
            return Conversation()
        with self.lock:
            now = time.monotonic()
            for key in list(self.sessions):
                if now - self.sessions[key].touched > self.ttl:
                    del self.sessions[key]
            if session_id not in self.sessions:
                self.sessions[session_id] = Conversation()
            self.sessions.move_to_end(session_id)
            result = self.sessions[session_id]
            result.touched = now
            while len(self.sessions) > self.max_sessions:
                self.sessions.popitem(last=False)
            return result


conversations = ConversationStore()
