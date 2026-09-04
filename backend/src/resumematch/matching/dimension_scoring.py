"""Validated Decimal scoring configuration for the remaining generic dimensions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import cast

import yaml


@dataclass(frozen=True)
class DimensionMatchScoring:
    version: str
    seniority: dict[str, Decimal]
    education_degree: dict[str, Decimal]
    education_field: dict[str, Decimal]
    education_weights: dict[str, Decimal]
    related_fields: dict[str, tuple[str, ...]]
    work_mode: dict[str, Decimal]
    location: dict[str, Decimal]
    location_weights: dict[str, Decimal]


def load_dimension_match_scoring(path: Path) -> DimensionMatchScoring:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if (
        not isinstance(raw, dict)
        or raw.get("dimension_match_scoring_version") != "dimension_match_scoring@1"
    ):
        raise ValueError("dimension match scoring version")
    seniority = _decimal_map(raw.get("seniority"), "seniority")
    education = _object(raw.get("education"), "education")
    location_work_mode = _object(raw.get("location_work_mode"), "location_work_mode")
    education_weights = _decimal_map(education.get("weights"), "education weights")
    location_weights = _decimal_map(location_work_mode.get("weights"), "location weights")
    if sum(education_weights.values(), Decimal("0")) != Decimal("1.00"):
        raise ValueError("education weights")
    if sum(location_weights.values(), Decimal("0")) != Decimal("1.00"):
        raise ValueError("location weights")
    related = _related_fields(education.get("related_fields"))
    return DimensionMatchScoring(
        "dimension_match_scoring@1",
        seniority,
        _decimal_map(education.get("degree_level"), "degree"),
        _decimal_map(education.get("field"), "field"),
        education_weights,
        related,
        _decimal_map(location_work_mode.get("work_mode"), "work mode"),
        _decimal_map(location_work_mode.get("location"), "location"),
        location_weights,
    )


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(name)
    return value


def _decimal_map(value: object, name: str) -> dict[str, Decimal]:
    raw = _object(value, name)
    if not all(isinstance(raw[key], str) for key in sorted(raw)):
        raise ValueError(name)
    result = {key: Decimal(cast(str, raw[key])) for key in sorted(raw)}
    if any(result[key] < 0 or result[key] > 1 for key in sorted(result)):
        raise ValueError(name)
    return result


def _related_fields(value: object) -> dict[str, tuple[str, ...]]:
    raw = _object(value, "related fields")
    result: dict[str, tuple[str, ...]] = {}
    for key, related in sorted(raw.items()):
        if not isinstance(related, list) or not all(isinstance(item, str) for item in related):
            raise ValueError("related fields")
        result[key] = tuple(sorted(related))
    return result
