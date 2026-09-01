"""Extraction result validation that never reflects candidate text."""

from resumematch.core.errors import ExtractionInsufficientTextError
from resumematch.core.schemas.extracted_text import ExtractedText


def require_sufficient_text(extracted: ExtractedText) -> None:
    if extracted.page_count > 0 and len(extracted.text) < 200:
        raise ExtractionInsufficientTextError(
            "Too little text was extracted. Re-export a text-based PDF or DOCX."
        )
