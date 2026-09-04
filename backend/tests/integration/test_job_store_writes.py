"""Public job posting writes are explicit and derive only public identity folds."""

from datetime import UTC, datetime

from sqlalchemy import create_engine, select

from resumematch.core.schemas.job import JobPosting
from resumematch.job.store.queries import insert_job_posting
from resumematch.job.store.schema import job_posting, metadata


def test_store_write_derives_and_persists_only_public_job_identity_fields() -> None:
    engine = create_engine("sqlite://")
    metadata.create_all(engine)
    posting = JobPosting(
        schema_version="job_posting/1",
        internal_id="fixture:one",
        source_id="fixture",
        source_external_id="one",
        company="Example Organization, Inc.",
        raw_title="Senior Backend Engineer",
        raw_description="Public job description",
        apply_url="https://example.invalid/jobs/one",
        normalized_title="backend engineer",
        normalized_location="Austin, Texas, US",
        ingested_at=datetime(2026, 9, 4, tzinfo=UTC),
    )

    with engine.begin() as connection:
        insert_job_posting(connection, posting)
        stored = connection.execute(select(job_posting)).mappings().one()

    assert stored["company_fold"] == "example organization"
    assert stored["title_fold"] == "backend engineer"
    assert stored["location_fold"] == "austin, texas, us"
    assert "candidate_profile_json" not in stored
