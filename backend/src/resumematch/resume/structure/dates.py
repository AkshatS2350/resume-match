"""Month-granularity experience date parsing without wall-clock reads."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from resumematch.core.schemas.candidate import YearMonth

_MONTHS = {
    name: month
    for month, name in enumerate(
        ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"),
        1,
    )
}
_RANGE = re.compile(
    r"(?P<start>(?:(?:jan\w*|feb\w*|mar\w*|apr\w*|may|jun\w*|jul\w*|aug\w*|sep\w*|oct\w*|nov\w*|dec\w*)\s+\d{4}|\d{2}/\d{4}|\d{4}))\s*(?:-|–|to)\s*(?P<end>present|(?:(?:jan\w*|feb\w*|mar\w*|apr\w*|may|jun\w*|jul\w*|aug\w*|sep\w*|oct\w*|nov\w*|dec\w*)\s+\d{4}|\d{2}/\d{4}|\d{4}))",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedExperienceDates:
    start_date: YearMonth | None
    end_date: YearMonth | None
    is_present: bool
    duration_months: int | None
    date_conflict: bool


def _parse_month(value: str) -> YearMonth:
    lowered = value.lower()
    if "/" in lowered:
        month, year = lowered.split("/")
        return YearMonth(year=int(year), month=int(month))
    parts = lowered.split()
    if len(parts) == 1:
        return YearMonth(year=int(parts[0]), month=1)
    return YearMonth(year=int(parts[1]), month=_MONTHS[parts[0][:3]])


def _index(value: YearMonth) -> int:
    return value.year * 12 + value.month - 1


def parse_experience_dates(text: str, session_start_date: date) -> ParsedExperienceDates:
    """Parse one range; `present` resolves solely from supplied session data."""

    match = _RANGE.search(text)
    if match is None:
        return ParsedExperienceDates(None, None, False, None, False)
    start = _parse_month(match.group("start"))
    end_token = match.group("end").lower()
    is_present = end_token == "present"
    end = (
        YearMonth(year=session_start_date.year, month=session_start_date.month)
        if is_present
        else _parse_month(end_token)
    )
    duration = _index(end) - _index(start)
    if duration < 0:
        return ParsedExperienceDates(start, end, is_present, None, True)
    return ParsedExperienceDates(start, end, is_present, duration, False)
