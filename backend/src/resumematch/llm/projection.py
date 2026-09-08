"""Value-free RFC 6901 projection requests for the cloud-boundary gateway."""

from collections.abc import Mapping, Sequence
from typing import Literal, NewType

from pydantic import BaseModel, ConfigDict

from resumematch.core.schemas.sanitized import SanitizedResume

FieldPath = NewType("FieldPath", str)
LLMOperation = Literal[
    "explain_readiness",
    "explain_match",
    "generate_application_guidance",
    "summarize_skill_gaps",
    "bounded_extract",
]


class JobContext(BaseModel):
    """Public job fields allowed alongside a projection request."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    job_internal_id: str
    requirement_ids: tuple[str, ...]


class ProjectionRequest(BaseModel):
    """Caller-selected paths only; candidate-derived values have no field here."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    operation: LLMOperation
    sanitization_content_hash: str
    paths: tuple[FieldPath, ...]
    evidence_item_ids: tuple[str, ...]
    permitted_skill_ids: tuple[str, ...]
    non_candidate_context: JobContext | None


def jsonpointer_sort_key(path: FieldPath) -> tuple[str, ...]:
    """Return the decoded JSON-pointer token order used by deterministic admission."""

    return _tokens(path)


def resolves(sanitized: SanitizedResume, path: FieldPath) -> bool:
    """Return false, not an exception, for an invalid or absent JSON pointer."""

    try:
        resolve(sanitized, path)
    except (IndexError, KeyError, TypeError, ValueError):
        return False
    return True


def resolve(sanitized: SanitizedResume, path: FieldPath) -> object:
    """Resolve an RFC 6901 path against the canonical sanitized artifact."""

    current: object = sanitized.model_dump(mode="json")
    for token in _tokens(path):
        if isinstance(current, Mapping):
            current = current[token]
        elif isinstance(current, Sequence) and not isinstance(current, str):
            if not token.isdecimal():
                raise ValueError("array index must be decimal")
            current = current[int(token)]
        else:
            raise TypeError("pointer cannot descend into scalar")
    return current


def resolves_operation(sanitized: SanitizedResume, path: FieldPath) -> bool:
    """Return whether a resume-root operation path resolves without exposing wrapper data."""

    try:
        resolve_operation(sanitized, path)
    except (IndexError, KeyError, TypeError, ValueError):
        return False
    return True


def resolve_operation(sanitized: SanitizedResume, path: FieldPath) -> object:
    """Resolve an operation path relative to the sanitized resume payload root."""

    current: object = sanitized.resume.model_dump(mode="json")
    for token in _tokens(path):
        if isinstance(current, Mapping):
            current = current[token]
        elif isinstance(current, Sequence) and not isinstance(current, str):
            if not token.isdecimal():
                raise ValueError("array index must be decimal")
            current = current[int(token)]
        else:
            raise TypeError("pointer cannot descend into scalar")
    return current


def expand_operation_paths(sanitized: SanitizedResume, pattern: FieldPath) -> tuple[FieldPath, ...]:
    """Expand a resume-root wildcard path in deterministic JSON-pointer order."""

    matches: list[FieldPath] = []

    def visit(value: object, tokens: tuple[str, ...], built: tuple[str, ...]) -> None:
        if not tokens:
            matches.append(FieldPath("/" + "/".join(built)))
            return
        token, *remaining = tokens
        rest = tuple(remaining)
        if token == "*" and isinstance(value, Sequence) and not isinstance(value, str):
            for index, item in enumerate(value):
                visit(item, rest, (*built, str(index)))
        elif isinstance(value, Mapping) and token in value:
            visit(value[token], rest, (*built, token))

    visit(sanitized.resume.model_dump(mode="json"), _tokens(pattern), ())
    return tuple(sorted(matches, key=jsonpointer_sort_key))


def _tokens(path: FieldPath) -> tuple[str, ...]:
    value = str(path)
    if value == "":
        return ()
    if not value.startswith("/"):
        raise ValueError("JSON Pointer must start with /")
    return tuple(_unescape(token) for token in value[1:].split("/"))


def _unescape(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")
