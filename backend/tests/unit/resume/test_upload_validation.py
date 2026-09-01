import os
from pathlib import Path

import pytest

from resumematch.core.errors import ErrorCode, PipelineError
from resumematch.resume.upload import (
    MAX_UPLOAD_BYTES,
    reject_declared_size,
    stream_to_temp,
    validate_document_limits,
)


def test_declared_size_rejects_without_consuming_stream() -> None:
    consumed = False

    def chunks() -> object:
        nonlocal consumed
        consumed = True
        yield b"x"

    with pytest.raises(PipelineError) as raised:
        reject_declared_size(str(MAX_UPLOAD_BYTES + 1))
    assert raised.value.code is ErrorCode.FILE_TOO_LARGE
    assert consumed is False


def test_stream_rejects_when_limit_is_crossed_and_removes_temp_file(tmp_path: Path) -> None:
    with pytest.raises(PipelineError) as raised:
        stream_to_temp(iter((b"x" * MAX_UPLOAD_BYTES, b"x")), tmp_path)
    assert raised.value.code is ErrorCode.FILE_TOO_LARGE
    assert list(tmp_path.iterdir()) == []


def test_stream_creates_private_hex_named_file(tmp_path: Path) -> None:
    path = stream_to_temp(iter((b"%PDF-1.7\n",)), tmp_path)
    try:
        assert len(path.name) == 32 and int(path.name, 16) >= 0
        if os.name != "nt":
            assert path.stat().st_mode & 0o777 == 0o600
    finally:
        path.unlink()


def test_pdf_page_count_limit(tmp_path: Path) -> None:
    path = tmp_path / "many-pages.pdf"
    path.write_bytes(b"%PDF-1.7\n" + b"/Type /Page\n" * 16)
    with pytest.raises(PipelineError) as raised:
        validate_document_limits(path, "application/pdf")
    assert raised.value.code is ErrorCode.TOO_MANY_PAGES
