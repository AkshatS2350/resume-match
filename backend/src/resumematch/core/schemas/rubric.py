"""Closed declarative schema for role rubrics."""

from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExperienceBand(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    band_id: str
    min_years: Decimal
    max_years: Decimal | None
    score: Decimal


class EducationExpectations(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    min_degree_level: Literal["none", "associate", "bachelors", "masters", "doctorate"]
    preferred_fields: tuple[str, ...]
    required: bool


class CertificationExpectation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    certification_id: str
    required: bool
    weight: Decimal


SignalTargetType = Literal[
    "canonical_skill",
    "experience_band",
    "education_requirement",
    "certification",
    "closed_flag",
]


class SignalTargetRef(BaseModel):
    """A closed, typed target for a deterministic signal resolver."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    target_type: SignalTargetType
    target_id: str


class Signal(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    signal_id: str
    type: Literal["skill", "experience_band", "education", "certification", "flag"]
    target: SignalTargetRef
    weight: Decimal
    min_evidence_level: int
    required: bool
    penalty_points: Decimal | None = None

    @model_validator(mode="after")
    def target_matches_signal_type(self) -> Self:
        expected = {
            "skill": "canonical_skill",
            "experience_band": "experience_band",
            "education": "education_requirement",
            "certification": "certification",
            "flag": "closed_flag",
        }
        if self.target.target_type != expected[self.type]:
            raise ValueError("target_type must match signal type")
        if self.type == "flag" and self.target.target_id != "quantified_impact":
            raise ValueError("unknown closed flag")
        return self


class AlternativeGroup(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    group_id: str
    display: str
    weight: Decimal
    min_evidence_level: int
    members: tuple[str, ...]


class PenaltyCondition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    kind: Literal[
        "no_item_in_section",
        "signal_below_level",
        "all_signals_absent_in_category",
        "total_experience_below",
    ]
    section: (
        Literal[
            "skills",
            "experience",
            "education",
            "projects",
            "certifications",
            "achievements",
            "unclassified",
        ]
        | None
    ) = None
    threshold_months: int | None = Field(default=None, ge=0, strict=True)

    @model_validator(mode="after")
    def validates_required_condition_fields(self) -> Self:
        if self.kind == "no_item_in_section" and self.section is None:
            raise ValueError("section is required for no_item_in_section")
        if self.kind == "total_experience_below" and self.threshold_months is None:
            raise ValueError("threshold_months is required for total_experience_below")
        return self


class RubricPenalty(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    penalty_id: str
    applies_to_category: str
    points: Decimal
    condition: PenaltyCondition


class RubricCategory(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    category_id: str
    display: str | None = None
    weight: Decimal
    signals: tuple[Signal, ...]
    alternative_groups: tuple[AlternativeGroup, ...] = ()


class RoleRubric(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: Literal["role_rubric/1"]
    rubric_id: str
    role_id: str
    role_family: str
    domain_id: str
    seniority_id: str
    rubric_version: str
    status: Literal["draft", "reviewed", "stable"]
    weight_basis: str
    weight_basis_note: str
    experience_bands: tuple[ExperienceBand, ...]
    education_expectations: EducationExpectations
    certification_expectations: tuple[CertificationExpectation, ...]
    categories: tuple[RubricCategory, ...]
    penalties: tuple[RubricPenalty, ...]
