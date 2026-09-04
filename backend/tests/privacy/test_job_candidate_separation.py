"""Public-job ingestion must not retain candidate-scoped data."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from resumematch.core.clock import FixedClock
from resumematch.core.schemas.job import JobPosting
from resumematch.job.normalizer import JobNormalizer
from resumematch.job.source_api import RawPosting


def test_job_posting_rejects_candidate_identifiers() -> None:
    """A future candidate field must not become silently persistable job data."""
    with pytest.raises(ValidationError, match="candidate_profile_json"):
        JobPosting(
            schema_version="job_posting/1",
            internal_id="fixture:one",
            source_id="fixture",
            source_external_id="one",
            company="Example Organization",
            raw_title="Engineer",
            raw_description="Public role description",
            apply_url="https://example.invalid/jobs/one",
            ingested_at=datetime(2026, 9, 3, tzinfo=UTC),
            candidate_profile_json="candidate-marker",
        )


def test_normalization_failure_does_not_retain_candidate_marker() -> None:
    """Rejected input is reported only by public source and external identifiers."""
    marker = "candidate-marker-must-not-enter-job-data"
    raw = RawPosting(
        "bad-posting",
        {
            "source_id": "fixture",
            "title": "Engineer",
            "organization": "Example Organization",
            "description": marker,
            "apply_url": None,
        },
    )

    result = JobNormalizer(FixedClock(datetime(2026, 9, 3, tzinfo=UTC))).normalize((raw,))

    assert result.postings == ()
    assert result.validation_failures == (("fixture", "bad-posting"),)
    assert marker not in repr(result.validation_failures)
