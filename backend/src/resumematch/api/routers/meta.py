"""Non-candidate service metadata endpoints."""

from fastapi import APIRouter

from resumematch.job.adapters.catalog import permitted_sources

router = APIRouter()


@router.get("/health")
def health() -> dict[str, int | str]:
    return {"status": "ok", "rubric_count": 0, "source_count": 0}


@router.get("/meta/sources")
def sources() -> dict[str, object]:
    """Disclose configured source documentation before an ingestion run exists."""
    return {
        "sources_queried": [],
        "organization_count": 0,
        "data_age_seconds": None,
        "documentation_urls": {
            source.source_id: source.documentation_url for source in permitted_sources()
        },
    }
