"""Session-bound sanitization endpoints."""

from datetime import datetime
from typing import Annotated, Literal, Protocol, cast, runtime_checkable

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict

from resumematch.api.composition import ApplicationComponents, components_dependency
from resumematch.api.deps import require_confirmed_profile
from resumematch.core.errors import SanitizationIncompleteError, SessionNotFoundError
from resumematch.core.schemas.candidate import CandidateProfile
from resumematch.core.schemas.sanitized import SanitizedResume
from resumematch.privacy.sanitizer import sanitize_profile

router = APIRouter(prefix="/sessions")


@runtime_checkable
class SanitizationRecordView(Protocol):
    """Read-only, value-free record shape exposed by session state."""

    content_hash: str
    profile_revision: int
    produced_at: datetime
    pii_policy_version: str
    detector_versions: tuple[str, ...]
    placeholder_set_version: str
    removed_categories: tuple[str, ...]
    fail_safe_redaction_count: int


class SanitizationSummary(BaseModel):
    """Value-free summary of a completed session sanitization."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    content_hash: str
    profile_revision: int
    produced_at: str
    pii_policy_version: str
    detector_versions: tuple[str, ...]
    placeholder_set_version: str
    removed_categories: tuple[str, ...]
    fail_safe_redaction_count: int


class SanitizedResumeResult(BaseModel):
    """The complete sanitization result held only in current session state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_label: Literal["session_sanitization_result"]
    sanitization_result: SanitizedResume
    removed_categories: tuple[str, ...]
    fail_safe_redaction_count: int


def _session(
    token: str | None, components: ApplicationComponents
) -> tuple[object, SanitizationRecordView]:
    if token is None or (session := components.session_store.get(token)) is None:
        raise SessionNotFoundError("Session not found")
    if session.sanitized_resume is None or session.sanitization_record is None:
        raise SanitizationIncompleteError("Session has no sanitization result")
    record = session.sanitization_record
    if not isinstance(record, SanitizationRecordView):
        raise SanitizationIncompleteError("Session sanitization record is invalid")
    return session.sanitized_resume, record


@router.post("/sanitize", response_model=SanitizationSummary)
def sanitize(
    profile: Annotated[CandidateProfile, Depends(require_confirmed_profile)],
    components: Annotated[ApplicationComponents, Depends(components_dependency)],
    token: Annotated[str | None, Header(alias="X-Session-Token")],
) -> SanitizationSummary:
    if token is None or (session := components.session_store.get(token)) is None:
        raise SessionNotFoundError("Session not found")
    _, record = sanitize_profile(
        profile, components.pii_detector, session, components.clock, components.sanitizer
    )
    return SanitizationSummary(
        content_hash=record.content_hash,
        profile_revision=record.profile_revision,
        produced_at=record.produced_at.isoformat(),
        pii_policy_version=record.pii_policy_version,
        detector_versions=record.detector_versions,
        placeholder_set_version=record.placeholder_set_version,
        removed_categories=record.removed_categories,
        fail_safe_redaction_count=record.fail_safe_redaction_count,
    )


@router.get("/sanitized-resume", response_model=SanitizedResumeResult)
def sanitized_resume(
    token: Annotated[str | None, Header(alias="X-Session-Token")],
    components: Annotated[ApplicationComponents, Depends(components_dependency)],
) -> SanitizedResumeResult:
    resume, record = _session(token, components)
    return SanitizedResumeResult(
        artifact_label="session_sanitization_result",
        sanitization_result=cast(SanitizedResume, resume),
        removed_categories=record.removed_categories,
        fail_safe_redaction_count=record.fail_safe_redaction_count,
    )
