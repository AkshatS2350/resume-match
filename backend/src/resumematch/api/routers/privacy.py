"""Session-bound sanitization and consent-inspection endpoints."""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Annotated, Literal, Protocol, cast, runtime_checkable

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict

from resumematch.api.composition import ApplicationComponents, components_dependency
from resumematch.api.deps import require_confirmed_profile
from resumematch.api.dto.privacy import (
    ConsentResult,
    ConsentSubmission,
    ManifestEntry,
    OmissionRecord,
    PendingRequestProjection,
    RequestManifest,
)
from resumematch.core.errors import SanitizationIncompleteError, SessionNotFoundError
from resumematch.core.schemas.candidate import CandidateProfile
from resumematch.core.schemas.sanitized import SanitizedResume
from resumematch.core.session import Session
from resumematch.llm.gateway import record_consent
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


def _pending_session(token: str | None, components: ApplicationComponents) -> Session:
    if token is None or (session := components.session_store.get(token)) is None:
        raise SessionNotFoundError("Session not found")
    if session.pending_llm_request is None:
        raise SanitizationIncompleteError("Session has no pending cloud request")
    return session


def _operation_leaf_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    """Enumerate resume-root scalar leaves deterministically without exposing values."""

    descendants: list[str] = []
    if isinstance(value, Mapping):
        for key in sorted(value):
            descendants.extend(_operation_leaf_paths(value[key], f"{prefix}/{key}"))
        return tuple(descendants)
    if isinstance(value, Sequence) and not isinstance(value, str):
        for index, item in enumerate(value):
            descendants.extend(_operation_leaf_paths(item, f"{prefix}/{index}"))
        return tuple(descendants)
    return (prefix,)


def _omissions(session: Session) -> tuple[OmissionRecord, ...]:
    pending = session.pending_llm_request
    sanitized = session.sanitized_resume
    assert pending is not None and sanitized is not None
    included = tuple(field.path for field in pending.fields)
    budget_omitted = pending.budget_omitted_paths
    records: list[OmissionRecord] = []
    for path in _operation_leaf_paths(sanitized.resume.model_dump(mode="json")):
        is_included = any(
            path == included_path or path.startswith(f"{included_path}/")
            for included_path in included
        )
        if is_included:
            continue
        reason: Literal["not_required_by_operation", "omitted_for_budget"] = (
            "omitted_for_budget"
            if any(path == dropped or path.startswith(f"{dropped}/") for dropped in budget_omitted)
            else "not_required_by_operation"
        )
        records.append(OmissionRecord(path=path, reason=reason))
    return tuple(records)


@router.get("/llm-requests/pending", response_model=PendingRequestProjection)
def pending_llm_request(
    token: Annotated[str | None, Header(alias="X-Session-Token")],
    components: Annotated[ApplicationComponents, Depends(components_dependency)],
) -> PendingRequestProjection:
    session = _pending_session(token, components)
    pending = session.pending_llm_request
    assert pending is not None
    return PendingRequestProjection(
        request_id=pending.request_id,
        operation=pending.operation,
        fields=pending.fields,
        payload_hash=pending.payload_hash,
        provider_identity=pending.provider_identity,
        provider_locality=pending.provider_locality,
        admitted_at=pending.admitted_at,
        omissions=_omissions(session),
    )


@router.get("/llm-requests", response_model=RequestManifest)
def llm_request_manifest(
    token: Annotated[str | None, Header(alias="X-Session-Token")],
    components: Annotated[ApplicationComponents, Depends(components_dependency)],
) -> RequestManifest:
    if token is None or (session := components.session_store.get(token)) is None:
        raise SessionNotFoundError("Session not found")
    return RequestManifest(
        entries=tuple(
            ManifestEntry(
                manifest_version=entry.manifest_version,
                operation=entry.operation,
                field_paths=entry.field_paths,
                omitted_paths=entry.omitted_paths,
                omissions=tuple(
                    OmissionRecord(path=omission.path, reason=omission.reason)
                    for omission in entry.omissions
                ),
                payload_hash=entry.payload_hash,
                transmitted_at=entry.transmitted_at,
            )
            for entry in session.llm_manifest
        )
    )


@router.post("/llm-requests/{request_id}/consent", response_model=ConsentResult)
def consent_to_llm_request(
    request_id: str,
    submission: ConsentSubmission,
    token: Annotated[str | None, Header(alias="X-Session-Token")],
    components: Annotated[ApplicationComponents, Depends(components_dependency)],
) -> ConsentResult:
    session = _pending_session(token, components)
    result = record_consent(
        session,
        request_id,
        submission.approved,
        components.llm_provider,
        clock=components.clock,
    )
    if (
        result is None
        or result.decided_at is None
        or result.decision not in {"declined", "unavailable", "transmitted"}
    ):
        raise SanitizationIncompleteError("Session has no matching pending cloud request")
    return ConsentResult(
        request_id=result.request_id,
        decision=cast(Literal["declined", "unavailable", "transmitted"], result.decision),
        decided_at=result.decided_at,
    )
