"""Deterministic public-posting duplicate handling without similarity matching."""

from __future__ import annotations

from resumematch.core.schemas.job import JobPosting
from resumematch.job.normalizer import company_fold


def deduplicate(postings: tuple[JobPosting, ...]) -> tuple[JobPosting, ...]:
    newest: dict[tuple[str, str], JobPosting] = {}
    for posting in postings:
        source_key = (posting.source_id, posting.source_external_id)
        existing = newest.get(source_key)
        if existing is None or posting.ingested_at > existing.ingested_at:
            newest[source_key] = posting
    groups: dict[tuple[str, str | None, str | None], list[JobPosting]] = {}
    for posting in newest.values():
        key = (company_fold(posting.company), posting.normalized_title, posting.normalized_location)
        groups.setdefault(key, []).append(posting)
    resolved: list[JobPosting] = []
    for group in groups.values():
        primary = min(group, key=lambda posting: posting.internal_id)
        group_id = primary.internal_id if len(group) > 1 else None
        resolved.extend(
            posting.model_copy(
                update={"duplicate_group_id": group_id, "is_primary_in_group": posting is primary}
            )
            for posting in group
        )
    return tuple(sorted(resolved, key=lambda posting: posting.internal_id))
