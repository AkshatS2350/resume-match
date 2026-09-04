import json
from datetime import UTC, datetime
from pathlib import Path

from resumematch.core.schemas.job import JobPosting


def test_job_posting_has_only_public_job_inputs_and_round_trips() -> None:
    posting = JobPosting(
        schema_version="job_posting/1", internal_id="job-1", source_id="fixture",
        source_external_id="source-1", company="Example", raw_title="Engineer",
        raw_description="Description", apply_url="https://example.test/apply",
        normalized_title=None, role_family=None, seniority=None, normalized_location=None,
        raw_location=None, work_mode=None, employment_type=None, required_skills=(),
        preferred_skills=(), min_experience_years=None, max_experience_years=None,
        experience_conflict=False, education_requirements=(), certification_requirements=(),
        requirements=(), posted_at=None, ingested_at=datetime(2026, 1, 1, tzinfo=UTC),
        duplicate_group_id=None, is_primary_in_group=True,
    )
    assert JobPosting.model_validate_json(posting.model_dump_json()) == posting
    field_names = set(JobPosting.model_fields)
    required = {
        "internal_id", "source_id", "source_external_id", "company", "raw_title",
        "raw_description", "apply_url",
    }
    assert required <= field_names
    assert not {"session", "profile", "candidate", "evidence", "match"}.intersection(field_names)


def test_job_posting_schema_is_published() -> None:
    root = Path(__file__).resolve().parents[3]
    schema_path = root / "docs" / "schemas" / "job_posting.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["title"] == "JobPosting"
