"""Deterministic, configuration-backed job seniority derivation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import yaml

from resumematch.core.schemas.candidate import SeniorityId

_NON_WORD = re.compile(r"[^\w\s]")
_SPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class SeniorityResolution:
    seniority: SeniorityId
    mapping_version: str


@dataclass(frozen=True)
class SeniorityMapping:
    version: str
    order: tuple[str, ...]
    enum_values: dict[str, SeniorityId]
    strong_levels: frozenset[str]
    title_tokens: dict[str, tuple[str, ...]]
    experience_thresholds: dict[str, tuple[Decimal, Decimal | None]]
    max_only_thresholds: dict[str, Decimal]
    fallback: SeniorityId


def derive_seniority(
    title: str,
    minimum_years: Decimal | None,
    maximum_years: Decimal | None,
    config_path: Path,
) -> SeniorityResolution:
    """Resolve title, then experience, using only the supplied versioned mapping."""
    mapping = load_seniority_mapping(config_path)
    title_level = _title_level(title, mapping)
    if title_level is not None and title_level in mapping.strong_levels:
        return SeniorityResolution(mapping.enum_values[title_level], mapping.version)

    experience_level = _experience_level(minimum_years, maximum_years, mapping)
    if experience_level is not None:
        return SeniorityResolution(mapping.enum_values[experience_level], mapping.version)
    if title_level is not None:
        return SeniorityResolution(mapping.enum_values[title_level], mapping.version)
    return SeniorityResolution(mapping.fallback, mapping.version)


def load_seniority_mapping(path: Path) -> SeniorityMapping:
    """Load the checked-in mapping into deterministic, typed lookup structures."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("seniority mapping must be an object")
    order = _strings(raw, "seniority_order")
    enum_values = {
        level: SeniorityId(value)
        for level, value in sorted(_mapping(raw, "enum_values").items())
        if isinstance(value, str)
    }
    if set(order) != set(enum_values):
        raise ValueError("every seniority level must have an enum value")
    return SeniorityMapping(
        version=_string(raw, "seniority_mapping_version"),
        order=order,
        enum_values=enum_values,
        strong_levels=frozenset(_strings(raw, "strong_title_levels")),
        title_tokens={
            level: _string_tuple(tokens)
            for level, tokens in sorted(_mapping(raw, "title_tokens").items())
        },
        experience_thresholds={
            level: _threshold_bounds(threshold)
            for level, threshold in sorted(_mapping(raw, "experience_thresholds").items())
        },
        max_only_thresholds={
            level: _max_only_threshold(threshold)
            for level, threshold in sorted(_mapping(raw, "max_only_thresholds").items())
        },
        fallback=SeniorityId(_string(raw, "fallback")),
    )


def _title_level(title: str, mapping: SeniorityMapping) -> str | None:
    folded_title = _fold(title)
    matched = [
        level
        for level in mapping.order
        if any(
            _contains_phrase(folded_title, _fold(token)) for token in mapping.title_tokens[level]
        )
    ]
    return max(matched, key=mapping.order.index) if matched else None


def _experience_level(
    minimum_years: Decimal | None, maximum_years: Decimal | None, mapping: SeniorityMapping
) -> str | None:
    if minimum_years is not None:
        for level in mapping.order:
            threshold = mapping.experience_thresholds.get(level)
            if (
                threshold is not None
                and minimum_years >= threshold[0]
                and (threshold[1] is None or minimum_years < threshold[1])
            ):
                return level
    if maximum_years is not None:
        for level in mapping.order:
            ceiling = mapping.max_only_thresholds.get(level)
            if ceiling is not None and maximum_years <= ceiling:
                return level
    return None


def _fold(value: str) -> str:
    return _SPACE.sub(" ", _NON_WORD.sub(" ", value.casefold())).strip()


def _contains_phrase(value: str, phrase: str) -> bool:
    return f" {phrase} " in f" {value} "


def _string(raw: dict[str, object], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _strings(raw: dict[str, object], key: str) -> tuple[str, ...]:
    value = raw.get(key)
    return _string_tuple(value)


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("mapping value must be a list of strings")
    return tuple(value)


def _mapping(raw: object, key: str) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise ValueError(f"{key} must be an object")
    value = raw.get(key)
    if not isinstance(value, dict) or not all(isinstance(name, str) for name in value):
        raise ValueError(f"{key} must be an object")
    return value


def _threshold_bounds(value: object) -> tuple[Decimal, Decimal | None]:
    if not isinstance(value, dict):
        raise ValueError("experience threshold must be an object")
    threshold = value
    lower = Decimal(str(threshold["min_years_gte"]))
    upper = threshold.get("min_years_lt")
    return lower, Decimal(str(upper)) if upper is not None else None


def _max_only_threshold(value: object) -> Decimal:
    if not isinstance(value, dict) or "max_years_lte" not in value:
        raise ValueError("maximum-only threshold must define max_years_lte")
    return Decimal(str(value["max_years_lte"]))
