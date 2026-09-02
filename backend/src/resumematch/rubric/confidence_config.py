"""Versioned exact-Decimal confidence configuration."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import cast

import yaml


class ConfidenceConfigError(ValueError):
    pass


def load_confidence_config(path: Path) -> dict[str, object]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != "confidence_weights@1":
        raise ConfidenceConfigError(f"{path}: version")
    for key in ("readiness_weights", "match_weights"):
        raw = data.get(key)
        if not isinstance(raw, dict):
            raise ConfidenceConfigError(f"{path}: {key}")
        typed_entries = sorted(raw.items())
        valid_entries = all(
            isinstance(name, str) and isinstance(value, str) for name, value in typed_entries
        )
        if not valid_entries:
            raise ConfidenceConfigError(f"{path}: {key}")
        typed_raw = cast(dict[str, str], raw)
        values = {name: Decimal(value) for name, value in sorted(typed_raw.items())}
        invalid_range = any(value < 0 or value > 1 for _, value in sorted(values.items()))
        total = sum(value for _, value in sorted(values.items()))
        invalid_sum = abs(total - Decimal("1")) > Decimal("0.001")
        if invalid_range or invalid_sum:
            raise ConfidenceConfigError(f"{path}: {key} weights")
        data[key] = values
    bands = data.get("bands")
    if not isinstance(bands, dict):
        raise ConfidenceConfigError(f"{path}: bands")
    low, high = Decimal(bands["low_medium"]), Decimal(bands["medium_high"])
    if not 0 <= low < high <= 1:
        raise ConfidenceConfigError(f"{path}: band thresholds")
    data["bands"] = {"low_medium": low, "medium_high": high}
    return data
