"""Closed declarative schema for role rubrics."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


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


class Signal(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    signal_id: str
    type: Literal["skill", "experience_band", "education", "certification", "flag"]
    canonical_skill_id: str | None = None
    weight: Decimal
    min_evidence_level: int
    required: bool
    penalty_points: Decimal | None = None


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
        "no_item_in_section", "signal_below_level", "all_signals_absent_in_category",
        "total_experience_below",
    ]
    section: str | None = None


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
