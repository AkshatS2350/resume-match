"""Session-scoped deterministic profile drafting and correction."""

from datetime import date
from decimal import Decimal
from typing import Annotated, TypeVar, cast

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict, field_validator

from resumematch.api.composition import ApplicationComponents, components_dependency
from resumematch.core.errors import SessionNotFoundError
from resumematch.core.schemas.candidate import (
    CandidateProfile,
    ExperienceItem,
    ItemBase,
    StructuredResume,
    TargetConstraints,
)
from resumematch.core.schemas.extracted_text import ExtractedText
from resumematch.resume.structure import structure
from resumematch.resume.structure.dates import recompute_experience_dates

router = APIRouter(prefix="/sessions/profile")
_Item = TypeVar("_Item", bound=ItemBase)


class ProfileUpdate(BaseModel):
    """The complete reviewed resume replacing the current session profile."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    resume: StructuredResume

    @field_validator("resume", mode="before")
    @classmethod
    def parse_json_resume(cls, value: object) -> StructuredResume:
        """Accept JSON transport values while preserving the frozen domain schema."""

        if isinstance(value, StructuredResume):
            return value
        return StructuredResume.model_validate(value, strict=False)


def _user_provided(item: _Item) -> _Item:
    return item.model_copy(
        update={
            "origin": "user_provided",
            "extraction_confidence": Decimal("1.00"),
            "provenance": None,
        }
    )


def _reviewed_items(current: tuple[_Item, ...], updated: tuple[_Item, ...]) -> tuple[_Item, ...]:
    current_by_id = {item.item_id: item for item in current}
    return tuple(
        item if current_by_id.get(item.item_id) == item else _user_provided(item)
        for item in updated
    )


def _recomputed_experience(item: ExperienceItem, session_start_date: date) -> ExperienceItem:
    dates = recompute_experience_dates(
        item.start_date,
        item.end_date,
        item.is_present,
        session_start_date,
    )
    return item.model_copy(
        update={
            "start_date": dates.start_date,
            "end_date": dates.end_date,
            "duration_months": dates.duration_months,
            "date_conflict": dates.date_conflict,
        }
    )


def _reviewed_resume(
    current: StructuredResume, updated: StructuredResume, session_start_date: date
) -> StructuredResume:
    experience = _reviewed_items(current.experience, updated.experience)
    return updated.model_copy(
        update={
            "skills": _reviewed_items(current.skills, updated.skills),
            "experience": tuple(
                _recomputed_experience(item, session_start_date) for item in experience
            ),
            "education": _reviewed_items(current.education, updated.education),
            "projects": _reviewed_items(current.projects, updated.projects),
            "certifications": _reviewed_items(current.certifications, updated.certifications),
            "achievements": _reviewed_items(current.achievements, updated.achievements),
            "unclassified": _reviewed_items(current.unclassified, updated.unclassified),
        }
    )


@router.post("/draft", response_model=StructuredResume)
def draft_profile(
    token: Annotated[str | None, Header(alias="X-Session-Token")],
    components: Annotated[ApplicationComponents, Depends(components_dependency)],
) -> StructuredResume:
    if token is None or (session := components.session_store.get(token)) is None:
        raise SessionNotFoundError("Session not found")
    if session.extracted_text is None:
        raise SessionNotFoundError("Session has no extracted resume")
    extracted = cast(ExtractedText, session.extracted_text)
    drafted = structure(
        extracted,
        session.session_start_date,
        components.section_headings,
        components.skill_normalizer,
    )
    session.structured_resume = drafted  # type: ignore[assignment]
    session.candidate_profile = CandidateProfile(
        schema_version="candidate_profile/1",
        profile_revision=session.profile_revision,
        session_start_date=session.session_start_date,
        resume=drafted,
        target=None,
        confirmed=False,
    )
    return drafted


@router.get("", response_model=CandidateProfile)
def get_profile(
    token: Annotated[str | None, Header(alias="X-Session-Token")],
    components: Annotated[ApplicationComponents, Depends(components_dependency)],
) -> CandidateProfile:
    if token is None or (session := components.session_store.get(token)) is None:
        raise SessionNotFoundError("Session not found")
    if session.candidate_profile is None:
        raise SessionNotFoundError("Session has no profile")
    return session.candidate_profile


@router.put("", response_model=CandidateProfile)
def update_profile(
    update: ProfileUpdate,
    token: Annotated[str | None, Header(alias="X-Session-Token")],
    components: Annotated[ApplicationComponents, Depends(components_dependency)],
) -> CandidateProfile:
    if token is None or (session := components.session_store.get(token)) is None:
        raise SessionNotFoundError("Session not found")
    if session.candidate_profile is None:
        raise SessionNotFoundError("Session has no profile")
    session.profile_revision += 1
    profile = session.candidate_profile
    updated = CandidateProfile(
        schema_version="candidate_profile/1",
        profile_revision=session.profile_revision,
        session_start_date=session.session_start_date,
        resume=_reviewed_resume(profile.resume, update.resume, session.session_start_date),
        target=profile.target,
        confirmed=False,
    )
    session.candidate_profile = updated
    session.structured_resume = updated.resume  # type: ignore[assignment]
    return updated


@router.post("/confirm", response_model=CandidateProfile)
def confirm_profile(
    target: TargetConstraints,
    token: Annotated[str | None, Header(alias="X-Session-Token")],
    components: Annotated[ApplicationComponents, Depends(components_dependency)],
) -> CandidateProfile:
    if token is None or (session := components.session_store.get(token)) is None:
        raise SessionNotFoundError("Session not found")
    if session.candidate_profile is None:
        raise SessionNotFoundError("Session has no profile")
    profile = session.candidate_profile
    confirmed = profile.model_copy(update={"target": target, "confirmed": True})
    session.candidate_profile = confirmed
    return confirmed
