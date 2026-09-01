"""Safe XML parsing primitives for hostile DOCX package members."""

from defusedxml.common import DefusedXmlException  # type: ignore[import-untyped]
from defusedxml.ElementTree import fromstring  # type: ignore[import-untyped]

from resumematch.core.errors import ExtractionFailedError


def parse_docx_xml(value: bytes) -> None:
    try:
        fromstring(value)
    except DefusedXmlException as error:
        raise ExtractionFailedError(
            "DOCX extraction failed. Re-export as a text-based DOCX."
        ) from error
