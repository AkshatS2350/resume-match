"""Typed, versioned configuration for deterministic signal resolvers."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from resumematch.core.schemas.candidate import DegreeLevel


class SignalResolverConfigError(ValueError):
    pass


class ExperienceBandTarget(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    band_id: str
    min_months: int
    max_months: int | None


class EducationTarget(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    target_id: str
    min_degree_level: DegreeLevel
    field_required: bool
    exact_field_ids: tuple[str, ...] = ()
    related_field_ids: tuple[str, ...] = ()


class CertificationTarget(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    certification_id: str
    equivalent_certification_ids: tuple[str, ...] = ()


class ResolverEvidenceLevels(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    skill: dict[str, int]
    experience_band: dict[str, int]
    education: dict[str, int]
    certification: dict[str, int]
    closed_flag: dict[str, dict[str, int]]


class SignalResolverConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    version: str
    resolver_evidence_level_version: str
    experience_bands: tuple[ExperienceBandTarget, ...]
    education_targets: tuple[EducationTarget, ...]
    certification_targets: tuple[CertificationTarget, ...]
    closed_flags: tuple[str, ...]
    evidence_levels: ResolverEvidenceLevels

    @field_validator("closed_flags")
    @classmethod
    def validate_flags(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if value != ("quantified_impact",):
            raise ValueError("closed_flags must contain only quantified_impact")
        return value


def load_signal_resolver_config(path: Path) -> SignalResolverConfig:
    try:
        config = SignalResolverConfig.model_validate(
            yaml.safe_load(path.read_text(encoding="utf-8"))
        )
    except (OSError, ValidationError, yaml.YAMLError) as error:
        raise SignalResolverConfigError(f"{path}: {error}") from error
    if config.version != "signal_resolvers@1":
        raise SignalResolverConfigError(f"{path}: version")
    if config.resolver_evidence_level_version != "resolver_evidence_level@1":
        raise SignalResolverConfigError(f"{path}: resolver_evidence_level_version")
    _validate_levels(config.evidence_levels)
    return config


def _validate_levels(levels: ResolverEvidenceLevels) -> None:
    all_levels = (
        *(value for _, value in sorted(levels.skill.items())),
        *(value for _, value in sorted(levels.experience_band.items())),
        *(value for _, value in sorted(levels.education.items())),
        *(value for _, value in sorted(levels.certification.items())),
        *(
            value
            for _, flag in sorted(levels.closed_flag.items())
            for _, value in sorted(flag.items())
        ),
    )
    if any(level not in {1, 2, 3} for level in all_levels):
        raise SignalResolverConfigError("evidence levels must be 1, 2, or 3")
