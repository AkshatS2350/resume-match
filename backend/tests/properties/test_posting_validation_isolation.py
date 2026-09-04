from datetime import UTC, datetime
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from resumematch.core.clock import FixedClock
from resumematch.job.adapters.fixture import FixtureJobSource
from resumematch.job.source_api import FetchRequest, RawPosting


def test_fixture_normalization_discards_only_the_malformed_posting() -> None:
    from resumematch.job.normalizer import JobNormalizer

    root = Path(__file__).resolve().parents[3]
    raw = (
        FixtureJobSource(root / "fixtures" / "jobs" / "default").fetch(FetchRequest(None)).postings
    )
    result = JobNormalizer(FixedClock(datetime(2026, 9, 3, tzinfo=UTC))).normalize(raw)

    assert len(result.postings) == 5
    assert result.validation_failures == (("fixture", None),)


def test_normalizer_rejects_a_posting_without_a_required_apply_url() -> None:
    from resumematch.job.normalizer import JobNormalizer

    raw = RawPosting(
        "missing-url",
        {
            "source_id": "fixture",
            "title": "Role",
            "organization": "Example Organization",
            "description": "Description",
        },
    )

    result = JobNormalizer(FixedClock(datetime(2026, 9, 3, tzinfo=UTC))).normalize((raw,))

    assert result.postings == ()
    assert result.validation_failures == (("fixture", "missing-url"),)


@given(st.lists(st.booleans(), min_size=1, max_size=12))
def test_normalizer_returns_exactly_the_valid_subset(flags: list[bool]) -> None:
    from resumematch.job.normalizer import JobNormalizer

    raw = tuple(
        RawPosting(
            f"posting-{index}",
            {
                "source_id": "fixture",
                "title": "Role",
                "organization": "Example Organization",
                "description": "Description",
                **({"apply_url": f"https://example.invalid/jobs/{index}"} if valid else {}),
            },
        )
        for index, valid in enumerate(flags)
    )
    result = JobNormalizer(FixedClock(datetime(2026, 9, 3, tzinfo=UTC))).normalize(raw)

    assert len(result.postings) == sum(flags)
    assert len(result.validation_failures) == len(flags) - sum(flags)
