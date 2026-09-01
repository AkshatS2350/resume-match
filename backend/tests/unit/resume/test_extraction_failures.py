from resumematch.core.errors import ErrorCode, PipelineError
from resumematch.core.schemas.extracted_text import ExtractedText
from resumematch.resume.extract.validation import require_sufficient_text


def test_short_extraction_is_rejected_without_reflecting_text() -> None:
    extracted = ExtractedText(
        text="candidate-derived marker" * 5,
        blocks=(),
        page_count=1,
        pages_with_text_layer=(1,),
        extractor_version="test",
    )
    try:
        require_sufficient_text(extracted)
    except PipelineError as error:
        assert error.code is ErrorCode.EXTRACTION_INSUFFICIENT_TEXT
        assert "candidate-derived marker" not in str(error)
    else:
        raise AssertionError("short extraction must fail")
