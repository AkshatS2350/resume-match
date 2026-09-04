from pathlib import Path


def test_fixture_adapter_returns_postings_in_manifest_order() -> None:
    from resumematch.job.adapters.fixture import FixtureJobSource
    from resumematch.job.source_api import FetchRequest

    root = Path(__file__).resolve().parents[4]
    result = FixtureJobSource(root / "fixtures" / "jobs" / "default").fetch(FetchRequest(None))

    assert [posting.source_external_id for posting in result.postings] == [
        "complete-1",
        "no-requirements-1",
        "conflict-1",
        "complete-1",
        "missing-1",
        None,
    ]
    assert result.failures == ()


def test_fixture_adapter_is_not_a_network_source() -> None:
    from resumematch.job.adapters.fixture import FixtureJobSource

    assert FixtureJobSource(Path("fixtures/jobs/default")).capabilities().is_network_source is False
