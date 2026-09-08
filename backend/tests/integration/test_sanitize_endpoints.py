from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from resumematch.api.app import app
from resumematch.core.schemas.candidate import CandidateProfile, StructuredResume


def _profile(*, confirmed: bool) -> CandidateProfile:
    return CandidateProfile(
        schema_version="candidate_profile/1",
        profile_revision=0,
        session_start_date=date(2026, 9, 9),
        resume=StructuredResume(
            schema_version="structured_resume/1",
            summary="ada@example.test",
            skills=(),
            experience=(),
            education=(),
            projects=(),
            certifications=(),
            achievements=(),
            unclassified=(),
        ),
        target=None,
        confirmed=confirmed,
    )


def _session_with_profile(*, confirmed: bool) -> tuple[TestClient, str]:
    client = TestClient(app)
    token = client.post("/api/v1/sessions").json()["token"]
    session = app.state.components.session_store.get(token)
    assert session is not None
    session.session_start_date = datetime(2026, 9, 9, tzinfo=UTC).date()
    session.candidate_profile = _profile(confirmed=confirmed)
    return client, token


def test_sanitize_rejects_an_unconfirmed_profile() -> None:
    client, token = _session_with_profile(confirmed=False)

    response = client.post("/api/v1/sessions/sanitize", headers={"X-Session-Token": token})

    assert response.status_code == 409
    assert response.json()["code"] == "PROFILE_NOT_CONFIRMED"


def test_sanitize_rejects_a_session_without_a_profile() -> None:
    client = TestClient(app)
    token = client.post("/api/v1/sessions").json()["token"]

    response = client.post("/api/v1/sessions/sanitize", headers={"X-Session-Token": token})

    assert response.status_code == 409
    assert response.json()["code"] == "PROFILE_NOT_CONFIRMED"


def test_sanitized_resume_requires_a_completed_sanitization() -> None:
    client = TestClient(app)
    token = client.post("/api/v1/sessions").json()["token"]

    response = client.get("/api/v1/sessions/sanitized-resume", headers={"X-Session-Token": token})

    assert response.status_code == 409
    assert response.json()["code"] == "SANITIZATION_INCOMPLETE"


def test_sanitize_returns_only_a_value_free_summary_and_session_result() -> None:
    client, token = _session_with_profile(confirmed=True)

    summary = client.post("/api/v1/sessions/sanitize", headers={"X-Session-Token": token})
    result = client.get("/api/v1/sessions/sanitized-resume", headers={"X-Session-Token": token})

    assert summary.status_code == result.status_code == 200
    assert "resume" not in summary.json()
    assert "ada@example.test" not in str(summary.json())
    assert summary.json()["detector_versions"] == [
        "pii_rules@1",
        "presidio@2.2.362+en_core_web_sm@3.8.0",
    ]
    assert result.json()["artifact_label"] == "session_sanitization_result"
    assert result.json()["sanitization_result"]["resume"]["summary"] == "[[EMAIL]]"
    assert result.json()["removed_categories"] == ["email"]
