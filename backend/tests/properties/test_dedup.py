import ast
from datetime import UTC, datetime
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from resumematch.core.schemas.job import JobPosting


def _posting(identifier: str, source: str, external: str, hour: int) -> JobPosting:
    return JobPosting(
        schema_version="job_posting/1",
        internal_id=identifier,
        source_id=source,
        source_external_id=external,
        company="Example Systems",
        raw_title="Backend Engineer",
        raw_description="Description",
        apply_url="https://example.invalid/jobs/" + identifier,
        normalized_title="backend engineer",
        normalized_location="remote",
        ingested_at=datetime(2026, 9, 3, hour, tzinfo=UTC),
    )


def test_deduplicate_keeps_the_latest_same_source_record_and_lowest_cross_source_primary() -> None:
    from resumematch.job.dedup import deduplicate

    result = deduplicate(
        (
            _posting("b", "fixture", "same", 1),
            _posting("a", "fixture", "same", 2),
            _posting("c", "other", "other", 1),
        )
    )

    assert [posting.internal_id for posting in result] == ["a", "c"]
    assert result[0].is_primary_in_group is True


@given(st.permutations(("z", "a", "m")))
def test_cross_source_duplicate_primary_is_independent_of_ingestion_order(
    order: tuple[str, str, str],
) -> None:
    """Changing fetch order must not change the public duplicate-group primary."""
    from resumematch.job.dedup import deduplicate

    postings = {
        "z": _posting("z", "source-a", "1", 1),
        "a": _posting("a", "source-b", "2", 1),
        "m": _posting("m", "source-c", "3", 1),
    }

    result = deduplicate(tuple(postings[identifier] for identifier in order))

    assert [posting.internal_id for posting in result if posting.is_primary_in_group] == ["a"]
    assert {posting.duplicate_group_id for posting in result} == {"a"}


def test_duplicate_detection_exposes_no_similarity_or_embedding_dependency() -> None:
    """The v1 deduplicator cannot gain forbidden similarity machinery unnoticed."""
    module = Path(__file__).parents[2] / "src" / "resumematch" / "job" / "dedup.py"

    tree = ast.parse(module.read_text(encoding="utf-8"))
    imported_modules = {
        alias.name.casefold()
        for node in ast.walk(tree)
        if isinstance(node, ast.Import | ast.ImportFrom)
        for alias in node.names
    }

    assert all("embedding" not in name and "similarity" not in name for name in imported_modules)
