"""Live-cache freshness must never age out the fixture closed loop."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine

from resumematch.core.clock import FixedClock
from resumematch.core.schemas.job import JobPosting
from resumematch.job.store.queries import current_postings_query, insert_job_posting
from resumematch.job.store.schema import metadata


def _posting(identifier: str, source_id: str, ingested_at: datetime) -> JobPosting:
    return JobPosting(
        schema_version="job_posting/1",
        internal_id=identifier,
        source_id=source_id,
        source_external_id=identifier,
        company="Example Organization",
        raw_title="Engineer",
        raw_description="Public role description",
        apply_url=f"https://example.invalid/jobs/{identifier}",
        ingested_at=ingested_at,
    )


def test_live_posting_older_than_the_configured_maximum_age_is_excluded() -> None:
    engine = create_engine("sqlite://")
    metadata.create_all(engine)
    clock = FixedClock(datetime(2030, 1, 1, tzinfo=UTC))
    with engine.begin() as connection:
        insert_job_posting(
            connection, _posting("live-old", "greenhouse", datetime(2029, 1, 1, tzinfo=UTC))
        )
        rows = (
            connection.execute(current_postings_query(clock, timedelta(days=30))).mappings().all()
        )

    assert rows == []


def test_fixture_postings_remain_visible_when_the_clock_is_years_later() -> None:
    engine = create_engine("sqlite://")
    metadata.create_all(engine)
    clock = FixedClock(datetime(2030, 1, 1, tzinfo=UTC))
    with engine.begin() as connection:
        for number in range(6):
            insert_job_posting(
                connection,
                _posting(f"fixture-{number}", "fixture", datetime(2025, 1, 1, tzinfo=UTC)),
            )
        rows = (
            connection.execute(current_postings_query(clock, timedelta(days=30))).mappings().all()
        )

    assert [row["internal_id"] for row in rows] == [f"fixture-{number}" for number in range(6)]
