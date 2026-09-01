from pathlib import Path

import pytest

from resumematch.core.errors import ErrorCode, PipelineError
from resumematch.resume.upload import DOCX_CONTENT_TYPE, PDF_CONTENT_TYPE, validate_document_limits

ROOT = Path(__file__).resolve().parents[4] / "fixtures" / "resumes" / "adversarial"


def test_compression_bomb_is_rejected_before_extraction() -> None:
    with pytest.raises(PipelineError) as raised:
        validate_document_limits(ROOT / "compression-bomb.docx", DOCX_CONTENT_TYPE)
    assert raised.value.code is ErrorCode.FILE_TOO_LARGE


def test_sixteen_page_pdf_is_rejected() -> None:
    with pytest.raises(PipelineError) as raised:
        validate_document_limits(ROOT / "sixteen-pages.pdf", PDF_CONTENT_TYPE)
    assert raised.value.code is ErrorCode.TOO_MANY_PAGES
