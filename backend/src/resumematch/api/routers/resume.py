"""The upload/extraction stage; raw bytes never enter session state."""

import tempfile
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Header, Request, UploadFile

from resumematch.api.composition import session_store_dependency
from resumematch.api.dto.resume import ExtractionResponse
from resumematch.core.errors import (
    EmptyFileError,
    ExtractionFailedError,
    FileTooLargeError,
    PipelineError,
    SessionNotFoundError,
)
from resumematch.core.session import SessionStore
from resumematch.resume.extract.docx import extract_docx
from resumematch.resume.extract.pdf import extract_pdf
from resumematch.resume.extract.text_layer import validate_text_layer
from resumematch.resume.extract.validation import require_sufficient_text
from resumematch.resume.upload import (
    MAX_UPLOAD_BYTES,
    PDF_CONTENT_TYPE,
    detect_content_type,
    extract_with_watchdog,
    reject_declared_size,
    validate_document_limits,
)

router = APIRouter(prefix="/sessions")


@router.post("/resume", response_model=ExtractionResponse)
async def upload_resume(
    request: Request,
    file: Annotated[UploadFile, File()],
    token: Annotated[str | None, Header(alias="X-Session-Token")],
    store: Annotated[SessionStore, Depends(session_store_dependency)],
) -> ExtractionResponse:
    if token is None or (session := store.get(token)) is None:
        raise SessionNotFoundError("Session not found")
    reject_declared_size(request.headers.get("content-length"))
    path = Path(tempfile.gettempdir()) / uuid.uuid4().hex
    total = 0
    try:
        with path.open("xb") as target:
            while chunk := await file.read(64 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise FileTooLargeError("The uploaded file exceeds the 10 MB limit")
                target.write(chunk)
        if total == 0:
            raise EmptyFileError("The uploaded file is empty")
        content_type = detect_content_type(path)
        validate_document_limits(path, content_type)
        extractor = extract_pdf if content_type == PDF_CONTENT_TYPE else extract_docx
        try:
            extracted = await extract_with_watchdog(extractor, path)
        except PipelineError:
            raise
        except Exception as error:
            label = "PDF" if content_type == PDF_CONTENT_TYPE else "DOCX"
            raise ExtractionFailedError(
                f"{label} extraction failed. Re-export as a text-based {label}."
            ) from error
        if content_type == PDF_CONTENT_TYPE:
            validate_text_layer(extracted)
        require_sufficient_text(extracted)
        session.extracted_text = extracted  # type: ignore[assignment]
        return ExtractionResponse(extraction_ok=True, page_count=extracted.page_count)
    finally:
        path.unlink(missing_ok=True)
