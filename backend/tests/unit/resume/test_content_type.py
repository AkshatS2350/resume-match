from pathlib import Path

import pytest

from resumematch.core.errors import ErrorCode, PipelineError
from resumematch.resume.upload import detect_content_type


def test_detects_pdf_by_magic_bytes_not_extension(tmp_path: Path) -> None:
    path = tmp_path / "resume.txt"
    path.write_bytes(b"%PDF-1.7\n")
    assert detect_content_type(path) == "application/pdf"


def test_rejects_zip_that_is_not_a_docx(tmp_path: Path) -> None:
    path = tmp_path / "renamed.pdf"
    path.write_bytes(b"PK\x03\x04not-a-docx")
    with pytest.raises(PipelineError) as raised:
        detect_content_type(path)
    assert raised.value.code is ErrorCode.UNSUPPORTED_FORMAT
