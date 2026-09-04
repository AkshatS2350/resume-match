"""The public-job database schema must have no route for candidate data."""

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, select

from resumematch.core.schemas.job import JobPosting
from resumematch.job.store.queries import insert_job_posting
from resumematch.job.store.schema import job_posting, metadata


def test_exactly_the_five_approved_public_job_tables_are_defined() -> None:
    assert set(metadata.tables) == {
        "job_posting",
        "job_requirement",
        "job_skill",
        "job_education_req",
        "source_registry_state",
    }


def test_job_posting_persists_the_approved_duplicate_identity_folds() -> None:
    posting = metadata.tables["job_posting"]

    assert {"company_fold", "title_fold", "location_fold"} <= set(posting.columns.keys())
    assert {tuple(index.columns.keys()) for index in posting.indexes} == {
        ("company_fold", "title_fold", "location_fold"),
    }


def test_schema_has_no_candidate_derived_columns_or_orm_base() -> None:
    forbidden = {
        "candidate_profile_json",
        "resume_text",
        "raw_resume",
        "extracted_text",
        "sanitized_resume",
        "session_id",
    }
    all_columns = {column.name for table in metadata.tables.values() for column in table.columns}
    schema_root = Path(__file__).parents[2] / "src" / "resumematch" / "job" / "store"
    source = "\n".join(path.read_text(encoding="utf-8") for path in schema_root.glob("*.py"))

    assert forbidden.isdisjoint(all_columns)
    assert "declarative_base" not in source
    assert "registry(" not in source


def test_sqlite_store_has_no_candidate_marker_or_resume_bytes(tmp_path: Path) -> None:
    """A public posting write cannot persist an unrelated candidate-side marker."""
    marker = "candidate-data-marker-must-not-persist"
    database = tmp_path / "public-jobs.sqlite3"
    engine = create_engine(f"sqlite:///{database}")
    metadata.create_all(engine)
    posting = JobPosting(
        schema_version="job_posting/1",
        internal_id="fixture:public",
        source_id="fixture",
        source_external_id="public",
        company="Example Organization",
        raw_title="Engineer",
        raw_description="Public role description",
        apply_url="https://example.invalid/jobs/public",
        ingested_at=datetime(2026, 9, 4, tzinfo=UTC),
    )

    with engine.begin() as connection:
        insert_job_posting(connection, posting)
        stored_text = " ".join(
            str(value)
            for row in connection.execute(select(job_posting)).mappings()
            for value in row.values()
            if isinstance(value, str)
        )

    assert marker not in stored_text
    assert marker.encode() not in database.read_bytes()
