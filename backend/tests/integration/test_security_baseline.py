from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from resumematch.api.app import create_app
from resumematch.api.ratelimit import TokenBucketLimiter, enforce_rate_limit


def test_unlisted_origins_never_receive_a_cors_wildcard() -> None:
    response = TestClient(create_app()).get(
        "/api/v1/openapi.json", headers={"Origin": "https://untrusted.example"}
    )

    assert response.headers.get("access-control-allow-origin") is None
    assert response.headers["strict-transport-security"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_token_bucket_rejects_requests_after_its_capacity_is_exhausted() -> None:
    limiter = TokenBucketLimiter(capacity=1, refill_per_second=0.01)

    assert limiter.allow("client")[0]
    allowed, retry_after = limiter.allow("client")

    assert not allowed
    assert retry_after > 0


def test_protected_endpoint_returns_a_rate_limited_error() -> None:
    router = APIRouter()

    @router.post("/protected", dependencies=[Depends(enforce_rate_limit)])
    def protected() -> dict[str, bool]:
        return {"ok": True}

    app = create_app(router)
    app.state.rate_limiter = TokenBucketLimiter(capacity=1, refill_per_second=0.01)
    client = TestClient(app)

    assert client.post("/api/v1/protected").status_code == 200
    response = client.post("/api/v1/protected")
    assert response.status_code == 429
    assert response.json()["code"] == "RATE_LIMITED"
