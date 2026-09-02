"""Public job-side schemas; these models never contain candidate-derived data."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


class ExtractedRequirement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    requirement_id: str
    classification: Literal["required", "preferred", "contextual"]
    low_confidence: bool
    canonical_skill_id: str | None
    unit_text: str
    start_offset: int
    end_offset: int
    unit_id: str
    excluded_category: Literal[
        "work_authorization", "visa_status", "sponsorship", "security_clearance_citizenship"
    ] | None
    pattern_set_version: str
    delimitation_version: str

    @model_validator(mode="after")
    def offsets_are_ordered(self) -> "ExtractedRequirement":
        if self.end_offset <= self.start_offset:
            raise ValueError("end_offset must be greater than start_offset")
        return self
