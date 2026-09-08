"""Public-job query boundary, intentionally separate from candidate-scoped state."""

from collections.abc import Sequence
from datetime import timedelta
from enum import Enum

from sqlalchemy import Connection, Select, insert, or_, select

from resumematch.core.clock import Clock
from resumematch.core.schemas.job import JobPosting
from resumematch.job.normalizer import company_fold, location_fold, title_fold
from resumematch.job.store.schema import job_posting


def postings_query() -> Select[tuple[object, ...]]:
    """Build the deterministic base query for cached public postings."""
    return select(job_posting).order_by(job_posting.c.internal_id)


def current_postings_query(clock: Clock, maximum_age: timedelta) -> Select[tuple[object, ...]]:
    """Return fresh live cache records plus every fixture record, in stable order."""
    cutoff = clock.now() - maximum_age
    return (
        postings_query()
        .where(
            or_(
                job_posting.c.source_id == "fixture",
                job_posting.c.ingested_at >= cutoff,
            )
        )
        .order_by(job_posting.c.internal_id)
    )


def public_columns() -> Sequence[str]:
    """Expose the persisted public columns for tests and migration review."""
    return tuple(job_posting.c.keys())


def insert_job_posting(connection: Connection, posting: JobPosting) -> None:
    """Persist a normalized public posting with deterministic duplicate-identity folds."""
    connection.execute(insert(job_posting).values(_posting_values(posting)))


def _posting_values(posting: JobPosting) -> dict[str, object]:
    location = posting.raw_location or posting.normalized_location
    return {
        "internal_id": posting.internal_id,
        "source_id": posting.source_id,
        "source_external_id": posting.source_external_id,
        "company": posting.company,
        "raw_title": posting.raw_title,
        "raw_description": posting.raw_description,
        "apply_url": posting.apply_url,
        "normalized_title": posting.normalized_title,
        "role_family": posting.role_family,
        "seniority": _enum_value(posting.seniority),
        "normalized_location": posting.normalized_location,
        "raw_location": posting.raw_location,
        "work_mode": _enum_value(posting.work_mode),
        "employment_type": _enum_value(posting.employment_type),
        "min_experience_years": posting.min_experience_years,
        "max_experience_years": posting.max_experience_years,
        "experience_conflict": posting.experience_conflict,
        "posted_at": posting.posted_at,
        "ingested_at": posting.ingested_at,
        "duplicate_group_id": posting.duplicate_group_id,
        "is_primary_in_group": posting.is_primary_in_group,
        "pattern_set_version": None,
        "delimitation_version": None,
        "company_fold": company_fold(posting.company),
        "title_fold": title_fold(posting.raw_title)[0],
        "location_fold": location_fold(location) if location else "",
    }


def _enum_value(value: Enum | None) -> str | None:
    return value.value if value is not None else None
