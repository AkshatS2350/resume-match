"""Deterministic admission boundary for LLM operations."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, overload, runtime_checkable

from resumematch.core.canonical_json import canonical_sha256
from resumematch.core.schemas.sanitized import SanitizedResume
from resumematch.core.session import Session
from resumematch.llm.budget import (
    BudgetExceeded,
    PayloadBudget,
    PayloadValue,
    ReducedPayload,
    reduce_to_budget,
)
from resumematch.llm.projection import (
    FieldPath,
    ProjectionRequest,
    expand_operation_paths,
    jsonpointer_sort_key,
    resolve_operation,
    resolves_operation,
)
from resumematch.llm.schemas.operations import OPERATION_SPECS


class AdmissionDenial(str, Enum):
    UNKNOWN_OPERATION = "unknown_operation"
    SANITIZATION_INCOMPLETE = "sanitization_incomplete"
    SANITIZATION_STALE = "sanitization_stale"
    SANITIZATION_HASH_MISMATCH = "sanitization_hash_mismatch"
    PROJECTION_PATH_UNKNOWN = "projection_path_unknown"
    REQUIRED_PATH_MISSING = "required_path_missing"
    SANITIZATION_RECORD_INVALID = "sanitization_record_invalid"


@runtime_checkable
class _SanitizationRecordView(Protocol):
    """Read-only record shape visible at the gateway boundary."""

    content_hash: str
    profile_revision: int


@dataclass(frozen=True)
class AdmissionDenied:
    reason: AdmissionDenial
    paths: tuple[FieldPath, ...] = ()


@dataclass(frozen=True)
class AdmittedPayload:
    payload: dict[FieldPath, PayloadValue]
    reduction: ReducedPayload


def admit_payload(
    payload: Mapping[FieldPath, PayloadValue],
    required_paths: frozenset[FieldPath],
    budget: PayloadBudget,
    optional_path_priority: tuple[FieldPath, ...] = (),
) -> AdmittedPayload | BudgetExceeded:
    reduced = reduce_to_budget(payload, required_paths, budget, optional_path_priority)
    if isinstance(reduced, BudgetExceeded):
        return reduced
    return AdmittedPayload(dict(reduced.included_payload), reduced)


@overload
def admit(operation: str, /) -> AdmissionDenied: ...


@overload
def admit(
    session: Session,
    /,
    request: ProjectionRequest,
    budget: PayloadBudget = PayloadBudget(10_000, "budget_priority@1"),
    optional_path_priority: tuple[FieldPath, ...] = (),
) -> AdmittedPayload | AdmissionDenied | BudgetExceeded: ...


def admit(
    operation: Session | str,
    request: ProjectionRequest | None = None,
    budget: PayloadBudget = PayloadBudget(10_000, "budget_priority@1"),
    optional_path_priority: tuple[FieldPath, ...] = (),
) -> AdmittedPayload | AdmissionDenied | BudgetExceeded:
    """Admit only exact, resume-root projections from a current sanitized session."""

    if isinstance(operation, str):
        if operation not in OPERATION_SPECS:
            return AdmissionDenied(AdmissionDenial.UNKNOWN_OPERATION)
        raise NotImplementedError("admission requires a sanitized session payload")

    if request is None:
        raise TypeError("request is required for session-backed admission")

    record = operation.sanitization_record
    sanitized = operation.sanitized_resume
    if record is None or sanitized is None:
        return AdmissionDenied(AdmissionDenial.SANITIZATION_INCOMPLETE)
    if not isinstance(record, _SanitizationRecordView):
        return AdmissionDenied(AdmissionDenial.SANITIZATION_RECORD_INVALID)
    if record.profile_revision != operation.profile_revision:
        return AdmissionDenied(AdmissionDenial.SANITIZATION_STALE)
    if request.sanitization_content_hash != record.content_hash:
        return AdmissionDenied(AdmissionDenial.SANITIZATION_HASH_MISMATCH)
    if canonical_sha256(sanitized.model_dump(mode="json")) != record.content_hash:
        return AdmissionDenied(AdmissionDenial.SANITIZATION_HASH_MISMATCH)

    unknown = tuple(
        sorted(
            (path for path in request.paths if not resolves_operation(sanitized, path)),
            key=jsonpointer_sort_key,
        )
    )
    if unknown:
        return AdmissionDenied(AdmissionDenial.PROJECTION_PATH_UNKNOWN, unknown)

    spec = OPERATION_SPECS[request.operation]
    required = _required_paths(sanitized, spec.required_candidate_paths)
    if isinstance(required, AdmissionDenied):
        return required
    paths = tuple(sorted(set(request.paths).union(required), key=jsonpointer_sort_key))
    payload = {path: _payload_value(resolve_operation(sanitized, path)) for path in paths}
    return admit_payload(payload, frozenset(required), budget, optional_path_priority)


def _required_paths(
    sanitized: SanitizedResume, patterns: tuple[FieldPath, ...]
) -> tuple[FieldPath, ...] | AdmissionDenied:
    """Expand every required pattern and deny an absent required path without aliases."""

    paths: list[FieldPath] = []
    for pattern in patterns:
        expanded = expand_operation_paths(sanitized, pattern)
        if not expanded:
            return AdmissionDenied(AdmissionDenial.REQUIRED_PATH_MISSING, (pattern,))
        paths.extend(expanded)
    return tuple(sorted(set(paths), key=jsonpointer_sort_key))


def _payload_value(value: object) -> PayloadValue:
    """Narrow JSON-compatible resolved values without transforming them."""

    if value is None or isinstance(value, str | int | bool):
        return value
    if isinstance(value, list | tuple):
        return tuple(_payload_value(item) for item in value)
    if isinstance(value, Mapping):
        return {str(key): _payload_value(item) for key, item in value.items()}
    raise TypeError("resolved sanitized value is not a payload value")
