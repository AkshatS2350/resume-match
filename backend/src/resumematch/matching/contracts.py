"""Versioned, generic primitives shared by all deterministic dimension scorers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, IntEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DimensionId(str, Enum):
    SKILLS = "skills"
    EXPERIENCE = "experience"
    ROLE_SIMILARITY = "role_similarity"
    SENIORITY = "seniority"
    EDUCATION = "education"
    LOCATION_WORKMODE = "location_workmode"
    DOMAIN_SIGNALS = "domain_signals"


class EnablementReason(str, Enum):
    ENABLED_BY_CONFIG = "enabled_by_config"
    DISABLED_BY_CONFIG = "disabled_by_config"
    INSUFFICIENT_CANDIDATE_DATA = "insufficient_candidate_data"
    INSUFFICIENT_JOB_DATA = "insufficient_job_data"
    NOT_APPLICABLE_TO_JOB = "not_applicable_to_job"
    BLOCKED_BY_HARD_REQUIREMENT = "blocked_by_hard_requirement"


class EvidenceLevel(IntEnum):
    LEVEL_0 = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3


class EnablementVerdict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    dimension_id: DimensionId
    enabled: bool
    reason: EnablementReason


class DimensionScore(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    dimension_id: DimensionId
    enabled: bool
    score: Decimal | None = Field(default=None, ge=Decimal("0.00"), le=Decimal("1.00"))
    weight: Decimal = Field(ge=Decimal("0.00"), le=Decimal("1.00"))
    weighted_score: Decimal | None = Field(default=None, ge=Decimal("0.00"), le=Decimal("1.00"))
    evidence_level: EvidenceLevel | None
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def validates_enablement_shape(self) -> DimensionScore:
        if not self.enabled:
            if self.score is not None or self.weighted_score is not None:
                raise ValueError("disabled dimensions require null scores")
            return self
        if self.score is None or self.weighted_score is None:
            raise ValueError("enabled dimensions require score and weighted_score")
        if self.weighted_score != self.score * self.weight:
            raise ValueError("weighted_score must equal score multiplied by weight")
        return self


class EvidenceRef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    item_id: str = Field(min_length=1)
    item_type: str = Field(min_length=1)
    evidence_level: EvidenceLevel
    dimension_id: DimensionId


class EvidenceIndex(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    by_dimension: dict[DimensionId, tuple[EvidenceRef, ...]] = Field(default_factory=dict)
    by_requirement_id: dict[str, tuple[EvidenceRef, ...]] = Field(default_factory=dict)
    evidence_index_version: str = Field(min_length=1)

    @field_validator("by_dimension", "by_requirement_id")
    @classmethod
    def sorts_references(
        cls, value: dict[object, tuple[EvidenceRef, ...]]
    ) -> dict[object, tuple[EvidenceRef, ...]]:
        return {
            key: tuple(
                sorted(
                    references,
                    key=lambda reference: (
                        reference.item_id,
                        reference.item_type,
                        reference.evidence_level,
                        reference.dimension_id.value,
                    ),
                )
            )
            for key, references in sorted(value.items(), key=lambda entry: str(entry[0]))
        }

    @model_validator(mode="after")
    def checks_dimension_references(self) -> EvidenceIndex:
        for dimension in sorted(self.by_dimension, key=lambda value: value.value):
            if any(
                reference.dimension_id is not dimension
                for reference in self.by_dimension[dimension]
            ):
                raise ValueError("evidence reference dimension must match its index")
        return self


class MatchConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    matching_contract_version: str = Field(min_length=1)
    enablement_rules_version: str = Field(min_length=1)
    dimension_weights: dict[DimensionId, Decimal]
    enabled_dimensions: tuple[DimensionId, ...]

    @model_validator(mode="after")
    def validates_dimensions(self) -> MatchConfig:
        configured = frozenset(DimensionId)
        if frozenset(self.dimension_weights) != configured:
            raise ValueError("dimension weights must contain every configured dimension")
        if not set(self.enabled_dimensions) <= configured:
            raise ValueError("enabled dimensions must be configured")
        if len(set(self.enabled_dimensions)) != len(self.enabled_dimensions):
            raise ValueError("enabled dimensions must be unique")
        return self


@dataclass(frozen=True)
class MatchingContract:
    version: str
    enablement_rules_version: str
    dimension_ids: frozenset[DimensionId]
    enabled_dimensions: tuple[DimensionId, ...]
    enablement_reasons: frozenset[EnablementReason]


def load_matching_contract(path: Path) -> MatchingContract:
    """Load and validate the closed generic matching contract configuration."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("matching contract must be an object")
    version = raw.get("matching_contract_version")
    if not isinstance(version, str) or version != "matching_contract@1":
        raise ValueError("matching contract version")
    enablement_version = raw.get("enablement_rules_version")
    if not isinstance(enablement_version, str) or not enablement_version:
        raise ValueError("enablement rules version")
    dimensions = _enum_set(raw.get("dimension_ids"), DimensionId, "dimension_ids")
    enabled_dimensions = _enum_tuple(
        raw.get("enabled_dimensions"), DimensionId, "enabled_dimensions"
    )
    reasons = _enum_set(raw.get("enablement_reasons"), EnablementReason, "enablement_reasons")
    if dimensions != frozenset(DimensionId):
        raise ValueError("dimension_ids must equal the configured v1 dimensions")
    if reasons != frozenset(EnablementReason):
        raise ValueError("enablement_reasons must equal the configured v1 reasons")
    if frozenset(enabled_dimensions) != dimensions or len(enabled_dimensions) != len(dimensions):
        raise ValueError("enabled_dimensions must contain every configured dimension once")
    return MatchingContract(version, enablement_version, dimensions, enabled_dimensions, reasons)


def _enum_set[E: Enum](value: object, enum_type: type[E], name: str) -> frozenset[E]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{name} must be a list of strings")
    try:
        return frozenset(enum_type(item) for item in value)
    except ValueError as error:
        raise ValueError(f"{name} contains an unknown value") from error


def _enum_tuple[E: Enum](value: object, enum_type: type[E], name: str) -> tuple[E, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{name} must be a list of strings")
    try:
        return tuple(enum_type(item) for item in value)
    except ValueError as error:
        raise ValueError(f"{name} contains an unknown value") from error
