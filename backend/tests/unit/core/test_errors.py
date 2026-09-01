
import pytest
from pydantic import ValidationError

from resumematch.core.errors import ErrorCode, ErrorResponse, PipelineStage


def test_taxonomy_contains_every_error_code_from_the_design_table() -> None:
    expected_codes = {
        "UNSUPPORTED_FORMAT", "FILE_TOO_LARGE", "TOO_MANY_PAGES", "EMPTY_FILE",
        "EXTRACTION_INSUFFICIENT_TEXT", "EXTRACTION_FAILED", "SCANNED_PDF_UNSUPPORTED",
        "SCANNED_PDF_PARTIAL", "EXTRACTION_TIMEOUT", "VALIDATION_FAILED",
        "PROFILE_NOT_CONFIRMED", "SANITIZATION_INCOMPLETE", "SANITIZATION_STALE",
        "SANITIZATION_HASH_MISMATCH", "PROJECTION_PATH_UNKNOWN", "PII_DETECTION_UNAVAILABLE",
        "RUBRIC_UNAVAILABLE", "SCORING_FAILED", "MATCHING_FAILED", "SESSION_NOT_FOUND",
        "SESSION_EXPIRED", "RATE_LIMITED", "CONFIG_INVALID",
        "INTERNAL_ERROR",
    }

    assert expected_codes == {code.value for code in ErrorCode}
    assert "guidance_unavailable" not in {code.value for code in ErrorCode}


def test_error_response_context_rejects_candidate_derived_values() -> None:
    response = ErrorResponse(
        code=ErrorCode.SESSION_NOT_FOUND,
        message="Session not found",
        stage=PipelineStage.BOOT,
        details=(),
        retryable=False,
        context={"attempt": 1},
    )
    assert response.context == {"attempt": 1}

    with pytest.raises(ValidationError):
        ErrorResponse(
            code=ErrorCode.SESSION_NOT_FOUND,
            message="Session not found",
            stage=PipelineStage.BOOT,
            details=(),
            retryable=False,
            context={"candidate": object()},
        )
