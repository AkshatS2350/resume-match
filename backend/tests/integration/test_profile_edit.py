from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal, TypedDict

from fastapi.testclient import TestClient
from httpx import Response
from hypothesis import given
from hypothesis import strategies as st

from resumematch.api.app import app
from resumematch.core.schemas.candidate import (
    AchievementItem,
    CandidateProfile,
    CertificationItem,
    DegreeLevel,
    EducationItem,
    ExperienceItem,
    ProjectItem,
    Provenance,
    SeniorityId,
    SkillItem,
    StructuredResume,
    TargetConstraints,
    UnclassifiedItem,
    WorkMode,
    YearMonth,
)
from resumematch.core.session import Session


def _provenance() -> Provenance:
    return Provenance(section_id="experience", block_ids=("block",), start_offset=0, end_offset=1)


class _ItemFields(TypedDict):
    item_id: str
    origin: Literal["extracted"]
    extraction_confidence: Decimal
    confidence_inputs: tuple[str, ...]
    provenance: Provenance
    source_text: str


def _base(item_id: str) -> _ItemFields:
    return {
        "item_id": item_id,
        "origin": "extracted",
        "extraction_confidence": Decimal("0.50"),
        "confidence_inputs": ("section",),
        "provenance": _provenance(),
        "source_text": item_id,
    }


def _resume() -> StructuredResume:
    return StructuredResume(
        schema_version="structured_resume/1",
        summary="Original",
        skills=(SkillItem(**_base("skill"), surface="Python", canonical_skill_id="python"),),
        experience=(
            ExperienceItem(
                **_base("experience"),
                employer="Example",
                title="Engineer",
                start_date=YearMonth(year=2024, month=1),
                end_date=YearMonth(year=2024, month=4),
                is_present=False,
                duration_months=3,
                description="Built systems",
                date_conflict=False,
            ),
        ),
        education=(
            EducationItem(
                **_base("education"),
                institution="Example University",
                degree_level=DegreeLevel.BACHELORS,
                field_of_study="Computer Science",
                start_date=None,
                end_date=None,
                coursework=(),
            ),
        ),
        projects=(ProjectItem(**_base("project"), name="Project", description="Description"),),
        certifications=(
            CertificationItem(
                **_base("certification"),
                name="Certificate",
                issuer="Issuer",
                issued=None,
            ),
        ),
        achievements=(AchievementItem(**_base("achievement"), text="Achievement"),),
        unclassified=(UnclassifiedItem(**_base("unclassified"), text="Unclassified"),),
    )


def _session_with_profile() -> tuple[TestClient, str, Session]:
    client = TestClient(app)
    token = client.post("/api/v1/sessions").json()["token"]
    session = app.state.components.session_store.get(token)
    assert session is not None
    session.session_start_date = datetime(2026, 1, 1, tzinfo=UTC).date()
    session.candidate_profile = CandidateProfile(
        schema_version="candidate_profile/1",
        profile_revision=0,
        session_start_date=session.session_start_date,
        resume=_resume(),
        target=None,
        confirmed=False,
    )
    return client, token, session


def _put(client: TestClient, token: str, resume: StructuredResume) -> Response:
    return client.put(
        "/api/v1/sessions/profile",
        headers={"X-Session-Token": token},
        json={"resume": resume.model_dump(mode="json")},
    )


def test_profile_update_marks_added_or_changed_items_and_supports_every_section() -> None:
    client, token, _ = _session_with_profile()
    original = _resume()
    changed = original.model_copy(
        update={
            "skills": (),
            "experience": (original.experience[0].model_copy(update={"title": "Senior Engineer"}),),
            "education": (),
            "projects": (),
            "certifications": (),
            "achievements": (),
            "unclassified": (
                original.unclassified[0].model_copy(update={"text": "Corrected unclassified"}),
                UnclassifiedItem(**_base("added-unclassified"), text="Added unclassified"),
            ),
        }
    )

    response = _put(client, token, changed)

    assert response.status_code == 200
    body = response.json()
    assert body["profile_revision"] == 1
    assert body["resume"]["skills"] == []
    assert body["resume"]["education"] == []
    assert body["resume"]["projects"] == []
    assert body["resume"]["certifications"] == []
    assert body["resume"]["achievements"] == []
    for item in (
        body["resume"]["experience"][0],
        *body["resume"]["unclassified"],
    ):
        assert item["origin"] == "user_provided"
        assert item["extraction_confidence"] == "1.00"
        assert item["provenance"] is None


@given(
    title=st.text(min_size=1, max_size=20),
    start_month=st.integers(1, 6),
    end_month=st.integers(7, 12),
)
def test_profile_edits_are_user_provided_and_experience_duration_is_consistent(
    title: str, start_month: int, end_month: int
) -> None:
    client, token, _ = _session_with_profile()
    original = _resume()
    experience = original.experience[0].model_copy(
        update={
            "title": title,
            "start_date": YearMonth(year=2024, month=start_month),
            "end_date": YearMonth(year=2024, month=end_month),
        }
    )

    response = _put(client, token, original.model_copy(update={"experience": (experience,)}))

    assert response.status_code == 200
    item = response.json()["resume"]["experience"][0]
    assert item["origin"] == "user_provided"
    assert item["extraction_confidence"] == "1.00"
    assert item["duration_months"] == end_month - start_month
    assert item["date_conflict"] is False


def test_profile_revision_strictly_increases_on_every_put_and_get_survives_reload() -> None:
    client, token, _ = _session_with_profile()
    resume = _resume()

    first = _put(client, token, resume)
    second = _put(client, token, resume)
    reloaded = TestClient(app).get("/api/v1/sessions/profile", headers={"X-Session-Token": token})

    assert first.status_code == second.status_code == reloaded.status_code == 200
    assert first.json()["profile_revision"] == 1
    assert second.json()["profile_revision"] == 2
    assert reloaded.json()["profile_revision"] == 2
    assert reloaded.json()["resume"] == second.json()["resume"]


def test_profile_confirmation_sets_target_and_confirmed() -> None:
    client, token, _ = _session_with_profile()

    response = client.post(
        "/api/v1/sessions/profile/confirm",
        headers={"X-Session-Token": token},
        json=TargetConstraints(
            domain_id="software",
            role_id="backend_engineer",
            seniority_id=SeniorityId.ENTRY,
            locations=("London",),
            work_modes=(WorkMode.HYBRID,),
        ).model_dump(mode="json"),
    )

    assert response.status_code == 200
    assert response.json()["confirmed"] is True
    assert response.json()["target"]["role_id"] == "backend_engineer"
