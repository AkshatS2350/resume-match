from datetime import date

from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from hypothesis import given
from hypothesis import strategies as st

from resumematch.api.app import create_app
from resumematch.api.deps import require_confirmed_profile
from resumematch.core.schemas.candidate import CandidateProfile, StructuredResume


def _unconfirmed_profile(revision: int) -> CandidateProfile:
    return CandidateProfile(
        schema_version="candidate_profile/1",
        profile_revision=revision,
        session_start_date=date(2026, 1, 1),
        resume=StructuredResume(
            schema_version="structured_resume/1",
            summary=None,
            skills=(),
            experience=(),
            education=(),
            projects=(),
            certifications=(),
            achievements=(),
            unclassified=(),
        ),
        target=None,
        confirmed=False,
    )


@given(revision=st.integers(min_value=0, max_value=10_000))
def test_unconfirmed_profiles_cannot_execute_readiness_or_matching(revision: int) -> None:
    executions = {"readiness": 0, "matching": 0}
    router = APIRouter()

    @router.post("/sessions/readiness")
    def readiness(_: CandidateProfile = Depends(require_confirmed_profile)) -> dict[str, bool]:
        executions["readiness"] += 1
        return {"ok": True}

    @router.post("/sessions/matches")
    def matching(_: CandidateProfile = Depends(require_confirmed_profile)) -> dict[str, bool]:
        executions["matching"] += 1
        return {"ok": True}

    application = create_app(router)
    client = TestClient(application)
    token = application.state.components.session_store.create()
    session = application.state.components.session_store.get(token)
    assert session is not None
    session.candidate_profile = _unconfirmed_profile(revision)

    headers = {"X-Session-Token": token}
    readiness_response = client.post("/api/v1/sessions/readiness", headers=headers)
    matching_response = client.post("/api/v1/sessions/matches", headers=headers)

    assert readiness_response.status_code == matching_response.status_code == 409
    assert readiness_response.json()["code"] == "PROFILE_NOT_CONFIRMED"
    assert matching_response.json()["code"] == "PROFILE_NOT_CONFIRMED"
    assert readiness_response.json()["stage"] == matching_response.json()["stage"] == "score"
    assert executions == {"readiness": 0, "matching": 0}


def test_confirmed_profile_reaches_a_protected_handler() -> None:
    executions = [0]
    router = APIRouter()

    @router.post("/sessions/readiness")
    def readiness(_: CandidateProfile = Depends(require_confirmed_profile)) -> dict[str, bool]:
        executions[0] += 1
        return {"ok": True}

    application = create_app(router)
    client = TestClient(application)
    token = application.state.components.session_store.create()
    session = application.state.components.session_store.get(token)
    assert session is not None
    session.candidate_profile = _unconfirmed_profile(1).model_copy(update={"confirmed": True})

    response = client.post("/api/v1/sessions/readiness", headers={"X-Session-Token": token})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert executions == [1]
