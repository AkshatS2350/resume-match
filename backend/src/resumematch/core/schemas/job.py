"""Public job-side schemas; these models never contain candidate-derived data."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from resumematch.core.schemas.candidate import (
    DegreeLevel,
    EmploymentType,
    SeniorityId,
    WorkMode,
)


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


class EducationRequirement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    degree_level: DegreeLevel | None = None
    field_of_study: str | None = None
    requirement_kind: Literal["required", "preferred"]


class JobPosting(BaseModel):
    """A stored public posting and its cached, derived requirement set."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["job_posting/1"]
    internal_id: str
    source_id: str
    source_external_id: str
    company: str
    raw_title: str
    raw_description: str
    apply_url: str
    normalized_title: str | None = None
    role_family: str | None = None
    seniority: SeniorityId | None = None
    normalized_location: str | None = None
    raw_location: str | None = None
    work_mode: WorkMode | None = None
    employment_type: EmploymentType | None = None
    required_skills: tuple[str, ...] = ()
    preferred_skills: tuple[str, ...] = ()
    min_experience_years: Decimal | None = None
    max_experience_years: Decimal | None = None
    experience_conflict: bool = False
    education_requirements: tuple[EducationRequirement, ...] = ()
    certification_requirements: tuple[str, ...] = ()
    requirements: tuple[ExtractedRequirement, ...] = ()
    posted_at: datetime | None = None
    ingested_at: datetime
    duplicate_group_id: str | None = None
    is_primary_in_group: bool = False
