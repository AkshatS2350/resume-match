"""Frozen candidate-side schema primitives; no persistence behaviour lives here."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
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


class YearMonth(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    year: int
    month: int

    @model_validator(mode="after")
    def valid_month(self) -> Self:
        if not 1 <= self.month <= 12:
            raise ValueError("month must be in 1..12")
        return self


class DegreeLevel(str, Enum):
    NONE = "none"
    ASSOCIATE = "associate"
    BACHELORS = "bachelors"
    MASTERS = "masters"
    DOCTORATE = "doctorate"


class WorkMode(str, Enum):
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"
    UNKNOWN = "unknown"


class SeniorityId(str, Enum):
    INTERN = "intern"
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"
    UNKNOWN = "unknown"


class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


class SkillItem(ItemBase):
    surface: str
    canonical_skill_id: str


class ExperienceItem(ItemBase):
    employer: str | None
    title: str | None
    start_date: YearMonth | None
    end_date: YearMonth | None
    is_present: bool
    duration_months: int | None
    description: str | None
    date_conflict: bool


class EducationItem(ItemBase):
    institution: str | None
    degree_level: DegreeLevel | None
    field_of_study: str | None
    start_date: YearMonth | None
    end_date: YearMonth | None
    coursework: tuple[str, ...]


class ProjectItem(ItemBase):
    name: str | None
    description: str | None


class CertificationItem(ItemBase):
    name: str | None
    canonical_certification_id: str | None = None
    issuer: str | None
    issued: YearMonth | None


class AchievementItem(ItemBase):
    text: str


class UnclassifiedItem(ItemBase):
    text: str


class StructuredResume(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["structured_resume/1"]
    summary: str | None
    skills: tuple[SkillItem, ...]
    experience: tuple[ExperienceItem, ...]
    education: tuple[EducationItem, ...]
    projects: tuple[ProjectItem, ...]
    certifications: tuple[CertificationItem, ...]
    achievements: tuple[AchievementItem, ...]
    unclassified: tuple[UnclassifiedItem, ...]


class TargetConstraints(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    domain_id: str
    role_id: str
    seniority_id: SeniorityId
    locations: tuple[str, ...]
    work_modes: tuple[WorkMode, ...]


class CandidateProfile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["candidate_profile/1"]
    profile_revision: int
    session_start_date: date
    resume: StructuredResume
    target: TargetConstraints | None
    confirmed: bool
