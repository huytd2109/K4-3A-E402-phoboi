from __future__ import annotations

import hashlib
import time

from phoboi.models import Analysis, Handoff
from phoboi.security import safe_question_ref


class HandoffRegistry:
    def __init__(self, cooldown_seconds: int = 300):
        self.cooldown_seconds = cooldown_seconds
        self._seen: dict[str, float] = {}

    def create(
        self,
        analysis: Analysis,
        content: str,
        reason_code: str,
        source_ids: list[str],
        *,
        original_message_url: str | None = None,
        ta_role_id: str | None = None,
    ) -> Handoff:
        fingerprint = hashlib.sha256(
            f"{reason_code}|{analysis.entities.model_dump_json()}|{','.join(sorted(source_ids))}".encode("utf-8")
        ).hexdigest()[:16]
        now = time.time()
        duplicate = fingerprint in self._seen and now - self._seen[fingerprint] < self.cooldown_seconds
        if not duplicate:
            self._seen[fingerprint] = now
        return Handoff(
            handoff_id=f"HO-{fingerprint}",
            reason_code=reason_code,
            question_ref=safe_question_ref(analysis.msg_id, content),
            entities=analysis.entities,
            related_source_ids=source_ids,
            original_message_url=original_message_url,
            ta_role_id=ta_role_id,
            deduplicated=duplicate,
        )

