from __future__ import annotations

from datetime import datetime

import pytest

from phoboi.models import OfficialSource


@pytest.fixture
def source_factory():
    def make(source_id: str, deadline: str, **overrides) -> OfficialSource:
        values = {
            "source_id": source_id,
            "source_url": f"https://demo.invalid/official/{source_id}",
            "source_type": "synthetic_demo",
            "published_by_role": "DEMO_ADMIN",
            "published_at": datetime.fromisoformat("2026-09-14T09:30:00+07:00"),
            "effective_from": datetime.fromisoformat("2026-09-14T09:30:00+07:00"),
            "task_id": "LAB_02",
            "task_aliases": ["LAB2", "LAB_2"],
            "cohort": "K4",
            "class_scope": "ALL",
            "logistics_type": "deadline",
            "deadline": datetime.fromisoformat(deadline),
            "supersedes": [],
            "status": "active",
            "is_fixture": True,
        }
        values.update(overrides)
        return OfficialSource.model_validate(values)

    return make

