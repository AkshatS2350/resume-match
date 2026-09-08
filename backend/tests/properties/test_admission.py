"""Properties of deterministic, session-backed LLM admission."""

from datetime import UTC, datetime
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from resumematch.core.canonical_json import canonical_sha256
from resumematch.core.schemas.candidate import (
    SeniorityId,
    StructuredResume,
    TargetConstraints,
    UnclassifiedItem,
)
from resumematch.core.schemas.sanitized import SanitizedResume
from resumematch.core.session import Session
from resumematch.core.session_write import SanitizationRecord, write_sanitization_record
from resumematch.llm.budget import BudgetExceeded, PayloadBudget
from resumematch.llm.gateway import AdmissionDenial, AdmissionDenied, AdmittedPayload, admit
from resumematch.llm.projection import FieldPath, LLMOperation, ProjectionRequest


def _sanitized() -> SanitizedResume:
    return SanitizedResume(
        schema_version="sanitized_resume/1",
        source_profile_revision=3,
        resume=StructuredResume(
            schema_version="structured_resume/1",
            summary=None,
            skills=(),
            experience=(),
            education=(),
            projects=(),
            certifications=(),
            achievements=(),
            unclassified=(
                UnclassifiedItem(
                    item_id="unclassified-1",
                    origin="user_provided",
                    extraction_confidence=Decimal("1.00"),
                    confidence_inputs=(),
                    provenance=None,
                    source_text="sanitized text",
                    text="sanitized text",
                ),
            ),
        ),
        target=TargetConstraints(
            domain_id="domain",
            role_id="role",
            seniority_id=SeniorityId.ENTRY,
            locations=(),
            work_modes=(),
        ),
        removed_span_counts={},
    )


def _session() -> tuple[Session, SanitizedResume]:
    sanitized = _sanitized()
    session = Session("token", datetime(2026, 1, 1, tzinfo=UTC))
    session.profile_revision = sanitized.source_profile_revision
    record = SanitizationRecord(
        content_hash=canonical_sha256(sanitized.model_dump(mode="json")),
        profile_revision=sanitized.source_profile_revision,
        produced_at=datetime(2026, 1, 1, tzinfo=UTC),
        pii_policy_version="pii_policy@1",
        detector_versions=("detector@1",),
        placeholder_set_version="placeholders@1",
        removed_categories=(),
        fail_safe_redaction_count=0,
    )
    write_sanitization_record(session, sanitized, record)
    return session, sanitized


def _request(
    content_hash: str,
    paths: tuple[FieldPath, ...] = (),
    operation: LLMOperation = "bounded_extract",
) -> ProjectionRequest:
    return ProjectionRequest(
        operation=operation,
        sanitization_content_hash=content_hash,
        paths=paths,
        evidence_item_ids=(),
        permitted_skill_ids=(),
        non_candidate_context=None,
    )


def test_admission_resolves_required_paths_at_resume_root_and_excludes_wrapper_metadata() -> None:
    session, sanitized = _session()
    admitted = admit(session, _request(canonical_sha256(sanitized.model_dump(mode="json"))))

    assert isinstance(admitted, AdmittedPayload)
    assert admitted.payload == {"/unclassified/0/text": "sanitized text"}
    assert "/source_profile_revision" not in admitted.payload
    assert "/removed_span_counts" not in admitted.payload


def test_missing_record_hash_and_revision_are_deterministically_denied() -> None:
    session, sanitized = _session()
    request = _request(canonical_sha256(sanitized.model_dump(mode="json")))

    missing = admit(Session("token", datetime(2026, 1, 1, tzinfo=UTC)), request)
    assert missing == AdmissionDenied(AdmissionDenial.SANITIZATION_INCOMPLETE)
    assert admit(session, _request("sha256:" + "0" * 64)) == AdmissionDenied(
        AdmissionDenial.SANITIZATION_HASH_MISMATCH
    )
    session.profile_revision += 1
    assert admit(session, request) == AdmissionDenied(AdmissionDenial.SANITIZATION_STALE)


def test_outer_wrapper_paths_and_missing_required_wildcards_fail_closed() -> None:
    session, sanitized = _session()
    content_hash = canonical_sha256(sanitized.model_dump(mode="json"))

    unknown = admit(session, _request(content_hash, (FieldPath("/source_profile_revision"),)))
    missing = admit(session, _request(content_hash, operation="summarize_skill_gaps"))

    assert unknown == AdmissionDenied(
        AdmissionDenial.PROJECTION_PATH_UNKNOWN, (FieldPath("/source_profile_revision"),)
    )
    assert missing == AdmissionDenied(
        AdmissionDenial.REQUIRED_PATH_MISSING, (FieldPath("/skills/*/canonical_id"),)
    )


def test_stored_artifact_hash_mismatch_is_denied_without_session_mutation() -> None:
    session, sanitized = _session()
    content_hash = canonical_sha256(sanitized.model_dump(mode="json"))
    record = session.sanitization_record
    assert isinstance(record, SanitizationRecord)
    changed = sanitized.model_copy(update={"removed_span_counts": {"email": 1}})
    write_sanitization_record(session, changed, record)
    before = (session.profile_revision, session.sanitized_resume, session.sanitization_record)

    result = admit(session, _request(content_hash))

    assert result == AdmissionDenied(AdmissionDenial.SANITIZATION_HASH_MISMATCH)
    current = (session.profile_revision, session.sanitized_resume, session.sanitization_record)
    assert current == before


def test_required_only_budget_overflow_is_typed_and_optional_values_reduce_exactly() -> None:
    session, sanitized = _session()
    request = _request(
        canonical_sha256(sanitized.model_dump(mode="json")),
        (FieldPath("/summary"), FieldPath("/unclassified/0/text")),
    )

    overflow = admit(session, request, PayloadBudget(1, "budget_priority@1"))
    reduced = admit(
        session,
        request,
        PayloadBudget(45, "budget_priority@1"),
        (FieldPath("/summary"),),
    )

    assert isinstance(overflow, BudgetExceeded)
    assert isinstance(reduced, AdmittedPayload)
    assert reduced.payload == {"/unclassified/0/text": "sanitized text"}
    assert reduced.reduction.dropped_paths == ("/summary",)


@given(st.permutations(("/summary", "/unclassified/0/text")))
def test_admission_is_independent_of_caller_path_order(paths: list[str]) -> None:
    session, sanitized = _session()
    content_hash = canonical_sha256(sanitized.model_dump(mode="json"))

    first = admit(session, _request(content_hash, tuple(FieldPath(path) for path in paths)))
    second = admit(
        session,
        _request(content_hash, tuple(FieldPath(path) for path in reversed(paths))),
    )

    assert first == second
