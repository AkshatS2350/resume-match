"""Validated shared Evidence_Level multipliers."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import yaml


class MultiplierConfigError(ValueError):
    """Raised when an evidence multiplier table is invalid."""


def load_multipliers(path: Path) -> dict[int, Decimal]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != "evidence_multipliers@1":
        raise MultiplierConfigError(f"{path}: version")
    raw = data.get("multipliers")
    if not isinstance(raw, dict) or set(raw) != {0, 1, 2, 3}:
        raise MultiplierConfigError(f"{path}: levels must be exactly 0, 1, 2, 3")
    values = {level: Decimal(value) for level, value in sorted(raw.items())}
    if values[0] != Decimal("0.00"):
        raise MultiplierConfigError(f"{path}: level 0 must be 0.0")
    if any(value < 0 or value > 1 for _, value in sorted(values.items())):
        raise MultiplierConfigError(f"{path}: values must be in [0, 1]")
    if any(values[level] > values[level + 1] for level in range(3)):
        raise MultiplierConfigError(f"{path}: values must be non-decreasing")
    return values
