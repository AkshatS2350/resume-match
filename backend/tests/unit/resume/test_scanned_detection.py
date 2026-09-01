from pathlib import Path

import pytest

from resumematch.core.errors import ErrorCode, PipelineError
from resumematch.core.schemas.extracted_text import ExtractedText
from resumematch.resume.extract.pdf import extract_pdf
from resumematch.resume.extract.text_layer import validate_text_layer


def test_image_only_pdf_is_rejected() -> None:
    path = Path(__file__).resolve().parents[4] / "fixtures" / "resumes" / "10-image-only.pdf"
    with pytest.raises(PipelineError) as raised:
        validate_text_layer(extract_pdf(path))
    assert raised.value.code is ErrorCode.SCANNED_PDF_UNSUPPORTED


def test_partially_scanned_pdf_reports_missing_pages() -> None:
    extracted = ExtractedText(
        text="text", blocks=(), page_count=3, pages_with_text_layer=(1,), extractor_version="test"
    )
    with pytest.raises(PipelineError) as raised:
        validate_text_layer(extracted)
    assert raised.value.code is ErrorCode.SCANNED_PDF_PARTIAL
    assert raised.value.context == {"affected_pages": "2,3"}
