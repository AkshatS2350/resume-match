"""Validated scoring configuration for deterministic matching."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import cast

import yaml


class MatchConfigError(ValueError):
    pass


DIMENSIONS = frozenset(
    {
        "skills", "experience", "role_similarity", "seniority", "education",
        "location_workmode", "domain_signals",
    }
)


def _load(path: Path, version: str) -> dict[str, object]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != version:
        raise MatchConfigError(f"{path}: version")
    return cast(dict[str, object], data)


def load_match_weights(path: Path) -> dict[str, Decimal]:
    data = _load(path, "match_weights@1")
    raw = data.get("weights")
    if not isinstance(raw, dict) or set(raw) != DIMENSIONS:
        raise MatchConfigError(f"{path}: dimensions")
    typed_entries = sorted(raw.items())
    if not all(isinstance(key, str) and isinstance(value, str) for key, value in typed_entries):
        raise MatchConfigError(f"{path}: weights")
    values = {key: Decimal(value) for key, value in sorted(cast(dict[str, str], raw).items())}
    invalid_range = any(value < 0 or value > 100 for _, value in sorted(values.items()))
    if invalid_range or sum(values.values(), Decimal("0")) != 100:
        raise MatchConfigError(f"{path}: weights")
    return values


def load_penalties(path: Path) -> tuple[Decimal, Decimal]:
    data = _load(path, "match_penalties@1")
    preferred = Decimal(cast(str, data.get("absent_preferred_requirement")))
    hard = Decimal(cast(str, data.get("absent_hard_requirement")))
    if preferred >= hard:
        raise MatchConfigError(f"{path}: preferred penalty must be less than hard penalty")
    return preferred, hard


def load_thresholds(path: Path) -> tuple[int, int]:
    data = _load(path, "match_thresholds@1")
    strong, stretch = data.get("strong_apply"), data.get("stretch")
    valid = isinstance(strong, int) and isinstance(stretch, int) and 0 <= stretch < strong <= 100
    if not valid:
        raise MatchConfigError(f"{path}: stretch < strong_apply in [0, 100]")
    assert isinstance(strong, int) and isinstance(stretch, int)
    return strong, stretch


def load_disqualification(path: Path) -> dict[str, object]:
    data = _load(path, "disqualification@1")
    threshold = data.get("unmet_required_threshold")
    tolerance = data.get("seniority_tolerance_years")
    categories = data.get("excluded_requirement_categories")
    if not isinstance(threshold, int) or not 1 <= threshold <= 10:
        raise MatchConfigError(f"{path}: unmet_required_threshold must be in [1, 10]")
    if not isinstance(tolerance, int) or not 0 <= tolerance <= 10:
        raise MatchConfigError(f"{path}: seniority_tolerance_years must be in [0, 10]")
    if not isinstance(categories, list) or len(categories) != 4:
        raise MatchConfigError(f"{path}: excluded_requirement_categories")
    return data


def load_equivalence_table(path: Path, version: str) -> dict[str, object]:
    """Load a versioned declarative equivalence table without score computation."""

    return _load(path, version)
