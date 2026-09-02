"""Deterministic quantified-impact detection independent of Evidence_Level."""

from __future__ import annotations

import re
from collections.abc import Collection
from dataclasses import dataclass

_VERSION = re.compile(r"\b\d+\.\d+(?:\.\d+)*\b")
_NUMBER = re.compile(r"\b\d+(?:[,.]\d+| \d{3})?")


@dataclass(frozen=True)
class QuantityMatch:
    """A configured quantity attributed to its containing candidate item."""

    item_id: str
    start_offset: int
    end_offset: int


def find_quantified_impacts(
    item_id: str,
    text: str,
    units: Collection[str],
    *,
    date_field_values: Collection[str] = (),
) -> tuple[QuantityMatch, ...]:
    """Find configured quantities, excluding dates and dotted versions.

    Date fields are supplied separately from the item's prose. A textual date value
    embedded in prose is also excluded, so a correction cannot become impact evidence.
    """

    ordered_units = sorted(set(units), key=lambda unit: (-len(unit), unit))
    if not ordered_units:
        return ()
    alternatives = "|".join(re.escape(unit) for unit in ordered_units)
    pattern = re.compile(rf"\b\d+(?:[,.]\d+| \d{{3}})? ?(?:{alternatives})\b|\b\d+%", re.I)
    version_ranges = {match.span() for match in _VERSION.finditer(text)}
    date_values = frozenset(date_field_values)
    matches: list[QuantityMatch] = []
    for match in pattern.finditer(text):
        if match.span() in version_ranges or match.group() in date_values:
            continue
        number_match = _NUMBER.match(match.group())
        if number_match is None:
            continue
        number = int(number_match.group().replace(",", "").replace(" ", "").split(".")[0])
        if 1900 <= number <= 2100:
            continue
        matches.append(QuantityMatch(item_id, match.start(), match.end()))
    return tuple(matches)


def quantified_impact(
    item_id: str,
    text: str,
    units: Collection[str],
    *,
    date_field_values: Collection[str] = (),
) -> bool:
    """Return whether an item has configured quantified impact.

    The detector intentionally has no Evidence_Level argument or dependency.
    """

    return bool(find_quantified_impacts(item_id, text, units, date_field_values=date_field_values))
