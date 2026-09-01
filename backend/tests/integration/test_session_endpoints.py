from fastapi.testclient import TestClient

from resumematch.api.app import create_app
from resumematch.api.routers.sessions import router


def test_session_token_uses_a_header_and_is_discarded() -> None:
    client = TestClient(create_app(router))
    created = client.post("/api/v1/sessions")

    assert created.status_code == 201
    token = created.json()["token"]
    assert len(token.encode()) >= 32
    assert all("{token}" not in route.path for route in client.app.routes)

    deleted = client.delete("/api/v1/sessions", headers={"X-Session-Token": token})
    assert deleted.status_code == 200
    missing = client.delete("/api/v1/sessions", headers={"X-Session-Token": token})
    assert missing.status_code == 404
    assert missing.json()["code"] == "SESSION_NOT_FOUND"
