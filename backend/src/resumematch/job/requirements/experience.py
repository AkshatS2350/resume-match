"""Deterministic extraction of stated job-experience ranges."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ExperienceRequirement:
    minimum_years: Decimal | None
    maximum_years: Decimal | None
    experience_conflict: bool


_RANGE = re.compile(r"\b(\d+)\s*(?:[-–]|to)\s*(\d+)\+?\s*(?:years|yrs)\b", re.I)
_MINIMUM = re.compile(r"\b(\d+)\+\s*(?:years|yrs)\b|\b(?:at least|minimum of)\s+(\d+)\b", re.I)


def extract_experience(text: str) -> ExperienceRequirement:
    ranges = [(int(match.group(1)), int(match.group(2))) for match in _RANGE.finditer(text)]
    minima = [
        int(group)
        for match in _MINIMUM.finditer(text)
        if (group := match.group(1) or match.group(2))
    ]
    all_minima = [minimum for minimum, _ in ranges] + minima
    if not all_minima:
        return ExperienceRequirement(None, None, False)
    minimum = min(all_minima)
    maximum = next((maximum for lower, maximum in ranges if lower == minimum), None)
    return ExperienceRequirement(
        minimum_years=Decimal(minimum),
        maximum_years=Decimal(maximum) if maximum is not None else None,
        experience_conflict=len(set(all_minima)) > 1,
    )
