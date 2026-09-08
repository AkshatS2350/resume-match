from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel

from resumematch.api.app import create_app
from resumematch.core.errors import ScoringFailedError, SessionNotFoundError


class _Body(BaseModel):
    quantity: int


def test_openapi_and_validation_errors_use_the_versioned_contract() -> None:
    router = APIRouter()

    @router.post("/validate")
    def validate(body: _Body) -> _Body:
        return body

    client = TestClient(create_app(router))
    document = client.get("/api/v1/openapi.json").json()
    response = client.post("/api/v1/validate", json={"quantity": "invalid"})

    assert all(path.startswith("/api/v1") for path in document["paths"])
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_FAILED"
    assert response.json()["details"]


def test_unhandled_error_uses_a_safe_internal_error_envelope() -> None:
    router = APIRouter()

    @router.get("/explode")
    def explode() -> None:
        raise RuntimeError("resume text: private@example.com")

    client = TestClient(create_app(router), raise_server_exceptions=False)
    response = client.get("/api/v1/explode")

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_ERROR",
        "message": "An internal error occurred. Please try again.",
        "stage": "any",
        "details": [],
        "retryable": True,
        "context": {},
    }


def test_known_pipeline_error_keeps_its_specific_code() -> None:
    router = APIRouter()

    @router.get("/missing")
    def missing() -> None:
        raise SessionNotFoundError("Session not found")

    response = TestClient(create_app(router)).get("/api/v1/missing")

    assert response.status_code == 404
    assert response.json()["code"] == "SESSION_NOT_FOUND"


def test_scoring_failure_returns_a_safe_score_stage_envelope() -> None:
    router = APIRouter()

    @router.get("/score")
    def score() -> None:
        raise ScoringFailedError("candidate-derived marker must not escape")

    response = TestClient(create_app(router)).get("/api/v1/score")

    assert response.status_code == 500
    assert response.json()["code"] == "SCORING_FAILED"
    assert response.json()["stage"] == "score"
    assert response.json()["retryable"] is True
    assert "candidate-derived marker" not in response.text
