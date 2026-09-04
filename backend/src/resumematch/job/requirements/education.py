"""Deterministic extraction of stated degree requirements from public job text."""

from __future__ import annotations

import re
from typing import Literal, cast

from resumematch.core.schemas.candidate import DegreeLevel

_EDUCATION = re.compile(
    r"\b(?P<degree>bachelor'?s|master'?s|associate|doctorate|ph\.?d\.?)\s+degree"
    r"(?:\s+in\s+(?P<field>[A-Za-z][A-Za-z ]*?))?\s+(?P<kind>required|preferred)\b",
    re.I,
)
_DEGREE_LEVELS = {
    "associate": DegreeLevel.ASSOCIATE,
    "bachelor's": DegreeLevel.BACHELORS,
    "bachelors": DegreeLevel.BACHELORS,
    "master's": DegreeLevel.MASTERS,
    "masters": DegreeLevel.MASTERS,
    "doctorate": DegreeLevel.DOCTORATE,
    "ph.d.": DegreeLevel.DOCTORATE,
    "phd": DegreeLevel.DOCTORATE,
}


def extract_education(
    text: str,
) -> tuple[tuple[DegreeLevel, str | None, Literal["required", "preferred"]], ...]:
    """Return degree requirements in source order without guessing missing fields."""
    return tuple(_education_requirement(match) for match in _EDUCATION.finditer(text))


def _education_requirement(
    match: re.Match[str],
) -> tuple[DegreeLevel, str | None, Literal["required", "preferred"]]:
    field = match.group("field")
    kind = match.group("kind").casefold()
    if kind not in {"required", "preferred"}:
        raise ValueError("education requirement kind")
    return (
        _DEGREE_LEVELS[match.group("degree").casefold()],
        field if isinstance(field, str) else None,
        cast(Literal["required", "preferred"], kind),
    )
