"""The v1 job-source catalog has an explicit, reviewable boundary."""

from pathlib import Path

from fastapi.testclient import TestClient

from resumematch.api.app import create_app
from resumematch.api.routers.meta import router
from resumematch.job.adapters.catalog import permitted_sources


def test_permitted_source_identifiers_are_the_v1_allowlist() -> None:
    """An unapproved source must not enter the catalog through a new adapter."""
    assert tuple(source.source_id for source in permitted_sources()) == (
        "greenhouse",
        "lever",
        "ashby",
        "adzuna",
        "usajobs",
        "fixture",
    )


def test_every_permitted_source_has_documentation_recorded() -> None:
    """Operators can verify every supported source against its public API documentation."""
    documentation = Path(__file__).parents[4] / "docs" / "job-sources.md"
    recorded = documentation.read_text(encoding="utf-8")

    for source in permitted_sources():
        assert source.documentation_url
        assert source.documentation_url in recorded


def test_source_metadata_discloses_current_coverage_without_claiming_ingestion() -> None:
    """Before a run, the public endpoint must distinguish permitted from queried sources."""
    response = TestClient(create_app(router)).get("/api/v1/meta/sources")

    assert response.status_code == 200
    assert response.json() == {
        "sources_queried": [],
        "organization_count": 0,
        "data_age_seconds": None,
        "documentation_urls": {
            source.source_id: source.documentation_url for source in permitted_sources()
        },
    }
