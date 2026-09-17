import os
from datetime import datetime, timezone

import pytest

from phoboi.config import Config
from phoboi.models import LogisticsType, OfficialSource, SourceStatus
from phoboi.pipeline import Pipeline
from phoboi.sources import SourceRepository


@pytest.fixture
def config():
    """A config with APP_ENV=test."""
    os.environ["APP_ENV"] = "test"
    return Config()


@pytest.fixture
def sample_official_sources():
    """Sample valid OfficialSource objects."""
    return [
        OfficialSource(
            source_id="src-1",
            source_url="http://discord.com/1",
            published_at=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
            task_id="lab-01",
            logistics_type=LogisticsType.DEADLINE,
            deadline=datetime(2026, 9, 10, 23, 59, tzinfo=timezone.utc),
            is_fixture=True,
            cohort="K4",
            class_scope="",
            status=SourceStatus.ACTIVE,
        ),
        OfficialSource(
            source_id="src-2",
            source_url="http://discord.com/2",
            published_at=datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc),
            task_id="lab-02",
            logistics_type=LogisticsType.DEADLINE,
            deadline=datetime(2026, 9, 15, 23, 59, tzinfo=timezone.utc),
            is_fixture=True,
            cohort="K4",
            class_scope="",
            status=SourceStatus.ACTIVE,
        ),
    ]


@pytest.fixture
def source_repo(config, sample_official_sources):
    """A loaded SourceRepository fixture."""
    repo = SourceRepository(config=config)
    repo._sources = sample_official_sources
    return repo


@pytest.fixture
def pipeline(config, source_repo):
    """A Pipeline fixture ready for E2E tests."""
    return Pipeline(config=config, source_repo=source_repo)
