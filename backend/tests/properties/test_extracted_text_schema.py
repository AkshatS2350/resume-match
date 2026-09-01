import json

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from resumematch.core.schemas.extracted_text import ExtractedBlock, ExtractedText


@given(st.text(min_size=1, max_size=30))
def test_extracted_text_round_trips(text: str) -> None:
    block = ExtractedBlock(
        block_id="1:1",
        section_id="preamble",
        page=1,
        start_offset=0,
        end_offset=len(text),
        text=text,
        layout_kind="paragraph",
        column_index=None,
    )
    value = ExtractedText(
        text=text,
        blocks=(block,),
        page_count=1,
        pages_with_text_layer=(1,),
        extractor_version="pdfplumber@1",
    )
    assert ExtractedText.model_validate(json.loads(value.model_dump_json())) == value


def test_block_rejects_non_positive_range() -> None:
    with pytest.raises(ValidationError):
        ExtractedBlock(
            block_id="1:1",
            section_id="preamble",
            page=1,
            start_offset=2,
            end_offset=2,
            text="x",
            layout_kind="paragraph",
            column_index=None,
        )
