from fastapi.testclient import TestClient

from resumematch.api.app import create_app
from resumematch.api.routers.meta import router


def test_health_exposes_only_non_candidate_service_metadata() -> None:
    response = TestClient(create_app(router)).get("/api/v1/health")

    assert response.status_code == 200
    assert set(response.json()) == {"status", "rubric_count", "source_count"}
