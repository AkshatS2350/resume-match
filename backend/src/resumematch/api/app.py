"""Application-startup safeguards for the single-worker deployment model."""

import os

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from resumematch.core.config import ConfigInvalid
from resumematch.core.errors import (
    ErrorCode,
    ErrorDetail,
    ErrorResponse,
    PipelineError,
    PipelineStage,
)

_WORKER_COUNT_VARIABLES = (
    "WEB_CONCURRENCY",
    "UVICORN_WORKERS",
    "GUNICORN_WORKERS",
)


def ensure_single_worker() -> None:
    """Reject a worker configuration incompatible with process-local sessions."""

    for variable in _WORKER_COUNT_VARIABLES:
        value = os.environ.get(variable)
        if value is None:
            continue
        try:
            workers = int(value)
        except ValueError as error:
            raise ConfigInvalid(f"invalid worker count for {variable}") from error
        if workers > 1:
            raise ConfigInvalid(
                f"{variable} must be unset or 1 because ResumeMatch uses a "
                "process-local SessionStore"
            )


ensure_single_worker()


_STATUS_BY_CODE = {
    ErrorCode.UNSUPPORTED_FORMAT: 415,
    ErrorCode.FILE_TOO_LARGE: 413,
    ErrorCode.TOO_MANY_PAGES: 400,
    ErrorCode.EMPTY_FILE: 400,
    ErrorCode.EXTRACTION_INSUFFICIENT_TEXT: 422,
    ErrorCode.EXTRACTION_FAILED: 422,
    ErrorCode.SCANNED_PDF_UNSUPPORTED: 422,
    ErrorCode.SCANNED_PDF_PARTIAL: 422,
    ErrorCode.EXTRACTION_TIMEOUT: 504,
    ErrorCode.VALIDATION_FAILED: 422,
    ErrorCode.PROFILE_NOT_CONFIRMED: 409,
    ErrorCode.SANITIZATION_INCOMPLETE: 409,
    ErrorCode.SANITIZATION_STALE: 409,
    ErrorCode.SANITIZATION_HASH_MISMATCH: 409,
    ErrorCode.PROJECTION_PATH_UNKNOWN: 400,
    ErrorCode.PII_DETECTION_UNAVAILABLE: 503,
    ErrorCode.RUBRIC_UNAVAILABLE: 409,
    ErrorCode.SCORING_FAILED: 500,
    ErrorCode.MATCHING_FAILED: 500,
    ErrorCode.SESSION_NOT_FOUND: 404,
    ErrorCode.SESSION_EXPIRED: 410,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.INTERNAL_ERROR: 500,
}


def _response(error: ErrorResponse, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=error.model_dump(mode="json"))


def create_app(*routers: APIRouter) -> FastAPI:
    """Create the versioned API shell; feature routers are added by their owning tasks."""

    application = FastAPI(openapi_url="/api/v1/openapi.json", docs_url=None, redoc_url=None)
    for router in routers:
        application.include_router(router, prefix="/api/v1")

    @application.exception_handler(RequestValidationError)
    async def validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
        details = tuple(
            ErrorDetail(field_path=".".join(str(part) for part in item["loc"]), message=item["msg"])
            for item in error.errors()
        )
        return _response(
            ErrorResponse(
                code=ErrorCode.VALIDATION_FAILED,
                message="Request validation failed.",
                stage=PipelineStage.ANY,
                details=details,
                retryable=False,
            ),
            422,
        )

    @application.exception_handler(PipelineError)
    async def pipeline_error(_: Request, error: PipelineError) -> JSONResponse:
        return _response(
            ErrorResponse(
                code=error.code,
                message=str(error),
                stage=PipelineStage.ANY,
                retryable=error.code
                in {ErrorCode.EXTRACTION_TIMEOUT, ErrorCode.PII_DETECTION_UNAVAILABLE},
                context=error.context,
            ),
            _STATUS_BY_CODE[error.code],
        )

    @application.exception_handler(Exception)
    async def internal_error(_: Request, __: Exception) -> JSONResponse:
        return _response(
            ErrorResponse(
                code=ErrorCode.INTERNAL_ERROR,
                message="An internal error occurred. Please try again.",
                stage=PipelineStage.ANY,
                retryable=True,
            ),
            500,
        )
    return application


app = create_app()
