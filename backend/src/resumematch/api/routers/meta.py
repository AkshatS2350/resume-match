"""Non-candidate service metadata endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, int | str]:
    return {"status": "ok", "rubric_count": 0, "source_count": 0}
