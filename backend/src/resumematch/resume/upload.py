"""Fail-closed upload validation primitives."""

import asyncio
import os
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from resumematch.core.errors import (
    ExtractionTimeoutError,
    FileTooLargeError,
    TooManyPagesError,
    UnsupportedFormatError,
)

PDF_CONTENT_TYPE = "application/pdf"
DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 15
EXTRACTION_TIMEOUT_SECONDS = 5


def reject_declared_size(content_length: str | None) -> None:
    if (
        content_length is not None
        and content_length.isdecimal()
        and int(content_length) > MAX_UPLOAD_BYTES
    ):
        raise FileTooLargeError("The uploaded file exceeds the 10 MB limit")


def stream_to_temp(chunks: Iterator[bytes], directory: Path) -> Path:
    path = directory / uuid.uuid4().hex
    total = 0
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.chmod(path, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as target:
            for chunk in chunks:
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise FileTooLargeError("The uploaded file exceeds the 10 MB limit")
                target.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


def detect_content_type(path: Path) -> str:
    with path.open("rb") as source:
        magic = source.read(5)
    if magic == b"%PDF-":
        return PDF_CONTENT_TYPE
    try:
        with ZipFile(path) as archive:
            if "[Content_Types].xml" in archive.namelist():
                return DOCX_CONTENT_TYPE
    except BadZipFile:
        pass
    raise UnsupportedFormatError("Only PDF and DOCX files are accepted")


def validate_document_limits(path: Path, content_type: str) -> None:
    if content_type == PDF_CONTENT_TYPE and path.read_bytes().count(b"/Type /Page") > MAX_PDF_PAGES:
        raise TooManyPagesError("PDF files may contain at most 15 pages")
    if content_type == DOCX_CONTENT_TYPE:
        with ZipFile(path) as archive:
            if sum(entry.file_size for entry in archive.infolist()) > MAX_UPLOAD_BYTES:
                raise FileTooLargeError("The uploaded file exceeds the 10 MB limit")


async def extract_with_watchdog[T](extractor: Callable[[Path], T], path: Path) -> T:
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(extractor, path), EXTRACTION_TIMEOUT_SECONDS
        )
    except TimeoutError as error:
        raise ExtractionTimeoutError("Extraction timed out. Please try again.") from error
