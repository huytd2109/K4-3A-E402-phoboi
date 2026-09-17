import os
from datetime import datetime, timezone
import pytest

from phoboi.config import Config
from phoboi.models import LogisticsType, OfficialSource, SourceStatus
from phoboi.sources import SourceRepository
from phoboi.sources.conflict_resolver import resolve_conflicts, ConflictResult


def test_source_repo_load_from_json(tmp_path):
    repo_file = tmp_path / "sources.json"
    repo_file.write_text("""
    [
        {
            "source_id": "src-file-1",
            "source_url": "http://discord/1",
            "published_at": "2026-09-01T10:00:00Z",
            "task_id": "lab-01",
            "logistics_type": "deadline",
            "deadline": "2026-09-10T23:59:00Z",
            "is_fixture": true
        }
    ]
    """)
    os.environ["APP_ENV"] = "test"
    config = Config()
    repo = SourceRepository(config=config)
    repo.load_from_file(repo_file)
    assert len(repo._sources) == 1
    assert repo._sources[0].source_id == "src-file-1"


def test_source_repo_query(source_repo):
    res = source_repo.query(task_id="lab-02", cohort="K4", class_scope="")
    assert len(res.sources) == 1
    assert res.sources[0].task_id == "lab-02"


def test_reject_fixtures_in_production(sample_official_sources, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    config = Config()
    repo = SourceRepository(config=config)
    with pytest.raises(ValueError, match="not allowed in production"):
        repo.load_from_list(sample_official_sources)


def test_conflict_two_active_sources_same_task_different_deadlines():
    s1 = OfficialSource(
        source_id="s1", source_url="http://a", published_at=datetime.now(timezone.utc),
        task_id="lab-01", logistics_type=LogisticsType.DEADLINE,
        deadline=datetime(2026, 9, 10, tzinfo=timezone.utc), is_fixture=True
    )
    s2 = OfficialSource(
        source_id="s2", source_url="http://b", published_at=datetime.now(timezone.utc),
        task_id="lab-01", logistics_type=LogisticsType.DEADLINE,
        deadline=datetime(2026, 9, 11, tzinfo=timezone.utc), is_fixture=True
    )
    res = resolve_conflicts([s1, s2])
    assert res.result == ConflictResult.CONFLICT


def test_supersedes_source_B_supersedes_A():
    s1 = OfficialSource(
        source_id="s1", source_url="http://a", published_at=datetime.now(timezone.utc),
        task_id="lab-01", logistics_type=LogisticsType.DEADLINE,
        deadline=datetime(2026, 9, 10, tzinfo=timezone.utc), is_fixture=True
    )
    s2 = OfficialSource(
        source_id="s2", source_url="http://b", published_at=datetime.now(timezone.utc),
        task_id="lab-01", logistics_type=LogisticsType.DEADLINE,
        deadline=datetime(2026, 9, 11, tzinfo=timezone.utc), is_fixture=True,
        supersedes="s1"
    )
    res = resolve_conflicts([s1, s2])
    assert res.result == ConflictResult.RESOLVED_BY_SUPERSEDE
    assert res.winner.source_id == "s2"


def test_revoked_sources_excluded():
    s1 = OfficialSource(
        source_id="s1", source_url="http://a", published_at=datetime.now(timezone.utc),
        task_id="lab-01", logistics_type=LogisticsType.DEADLINE,
        deadline=datetime(2026, 9, 10, tzinfo=timezone.utc), is_fixture=True,
        status=SourceStatus.REVOKED
    )
    res = resolve_conflicts([s1])
    # The conflict resolver ignores non-ACTIVE sources, so it will return NO_SOURCE
    assert res.result == ConflictResult.NO_SOURCE


def test_different_class_scopes_needs_clarification():
    s1 = OfficialSource(
        source_id="s1", source_url="http://a", published_at=datetime.now(timezone.utc),
        task_id="lab-01", logistics_type=LogisticsType.DEADLINE,
        class_scope="L2-3",
        deadline=datetime(2026, 9, 10, tzinfo=timezone.utc), is_fixture=True
    )
    s2 = OfficialSource(
        source_id="s2", source_url="http://b", published_at=datetime.now(timezone.utc),
        task_id="lab-01", logistics_type=LogisticsType.DEADLINE,
        class_scope="L3-4",
        deadline=datetime(2026, 9, 11, tzinfo=timezone.utc), is_fixture=True
    )
    res = resolve_conflicts([s1, s2])
    assert res.result == ConflictResult.NEEDS_CLASS_CLARIFICATION
