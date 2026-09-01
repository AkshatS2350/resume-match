"""Fail-closed scanned-PDF detection."""

from resumematch.core.errors import ScannedPdfPartialError, ScannedPdfUnsupportedError
from resumematch.core.schemas.extracted_text import ExtractedText


def validate_text_layer(extracted: ExtractedText) -> None:
    count = len(extracted.pages_with_text_layer)
    if count == 0:
        raise ScannedPdfUnsupportedError(
            "This PDF appears to be a scan. Upload a text-based PDF or DOCX."
        )
    if count * 2 < extracted.page_count:
        missing = ",".join(
            str(page)
            for page in range(1, extracted.page_count + 1)
            if page not in extracted.pages_with_text_layer
        )
        raise ScannedPdfPartialError(
            "This PDF is partially scanned. Upload a text-based PDF or DOCX.",
            context={"affected_pages": missing},
        )
