"""Frozen candidate-side schema primitives; no persistence behaviour lives here."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class Provenance(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    section_id: str
    block_ids: tuple[str, ...]
    start_offset: int
    end_offset: int

    @model_validator(mode="after")
    def ordered_offsets(self) -> Self:
        if self.end_offset <= self.start_offset:
            raise ValueError("end_offset must be greater than start_offset")
        return self


class ItemBase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    item_id: str
    origin: Literal["extracted", "user_provided"]
    extraction_confidence: Decimal
    confidence_inputs: tuple[str, ...]
    provenance: Provenance | None
    source_text: str

    @field_validator("extraction_confidence")
    @classmethod
    def valid_confidence(cls, value: Decimal) -> Decimal:
        if not Decimal("0") <= value <= Decimal("1"):
            raise ValueError("extraction_confidence must be in [0, 1]")
        exponent = value.as_tuple().exponent
        if not isinstance(exponent, int) or -exponent > 2:
            raise ValueError("extraction_confidence must have at most two decimal places")
        return value

    @model_validator(mode="after")
    def provenance_matches_origin(self) -> Self:
        if self.origin == "extracted" and self.provenance is None:
            raise ValueError("provenance is required for extracted items")
        if self.origin == "user_provided" and self.provenance is not None:
            raise ValueError("provenance must be absent for user_provided items")
        if self.origin == "user_provided" and self.extraction_confidence != Decimal("1.00"):
            raise ValueError("user_provided extraction_confidence must be 1.00")
        return self
