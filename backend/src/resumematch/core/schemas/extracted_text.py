"""Immutable extraction contracts with source-text offset invariants."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


class ExtractedBlock(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    block_id: str
    section_id: str
    page: int
    start_offset: int
    end_offset: int
    text: str
    layout_kind: Literal["paragraph", "list_item", "table_cell", "text_box", "heading"]
    column_index: int | None

    @model_validator(mode="after")
    def _offsets_are_a_nonempty_range(self) -> "ExtractedBlock":
        if self.end_offset <= self.start_offset:
            raise ValueError("end_offset must be greater than start_offset")
        return self


class ExtractedText(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str
    blocks: tuple[ExtractedBlock, ...]
    page_count: int
    pages_with_text_layer: tuple[int, ...]
    extractor_version: str
