"""Closed, candidate-safe error types shared by every pipeline stage."""

from collections.abc import Mapping
from enum import Enum

from pydantic import BaseModel, ConfigDict


class ErrorCode(str, Enum):
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    TOO_MANY_PAGES = "TOO_MANY_PAGES"
    EMPTY_FILE = "EMPTY_FILE"
    EXTRACTION_INSUFFICIENT_TEXT = "EXTRACTION_INSUFFICIENT_TEXT"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    SCANNED_PDF_UNSUPPORTED = "SCANNED_PDF_UNSUPPORTED"
    SCANNED_PDF_PARTIAL = "SCANNED_PDF_PARTIAL"
    EXTRACTION_TIMEOUT = "EXTRACTION_TIMEOUT"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    PROFILE_NOT_CONFIRMED = "PROFILE_NOT_CONFIRMED"
    SANITIZATION_INCOMPLETE = "SANITIZATION_INCOMPLETE"
    SANITIZATION_STALE = "SANITIZATION_STALE"
    SANITIZATION_HASH_MISMATCH = "SANITIZATION_HASH_MISMATCH"
    PROJECTION_PATH_UNKNOWN = "PROJECTION_PATH_UNKNOWN"
    PII_DETECTION_UNAVAILABLE = "PII_DETECTION_UNAVAILABLE"
    RUBRIC_UNAVAILABLE = "RUBRIC_UNAVAILABLE"
    SCORING_FAILED = "SCORING_FAILED"
    MATCHING_FAILED = "MATCHING_FAILED"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    RATE_LIMITED = "RATE_LIMITED"
    CONFIG_INVALID = "CONFIG_INVALID"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class PipelineStage(str, Enum):
    BOOT = "boot"
    UPLOAD = "upload"
    EXTRACT = "extract"
    STRUCTURE = "structure"
    SANITIZE = "sanitize"
    SCORE = "score"
    INGEST = "ingest"
    MATCH = "match"
    GUIDANCE = "guidance"
    ANY = "any"


class ErrorDetail(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    field_path: str | None = None
    message: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    code: ErrorCode
    message: str
    stage: PipelineStage
    details: tuple[ErrorDetail, ...] = ()
    retryable: bool = False
    context: Mapping[str, str | int] = {}


class PipelineError(Exception):
    """A fail-closed error with a stable machine-readable code."""

    code: ErrorCode

    def __init__(self, message: str, *, context: Mapping[str, str | int] | None = None) -> None:
        super().__init__(message)
        self.context = {} if context is None else dict(context)


def _error_type(name: str, code: ErrorCode) -> type[PipelineError]:
    return type(name, (PipelineError,), {"code": code})


for _code in ErrorCode:
    globals()["".join(part.title() for part in _code.value.split("_")) + "Error"] = _error_type(
        "".join(part.title() for part in _code.value.split("_")) + "Error", _code
    )

del _code
