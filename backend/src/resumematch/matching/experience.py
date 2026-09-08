"""Deterministic interval-union calculation for relevant experience."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_DOWN, Decimal

from resumematch.core.schemas.candidate import ExperienceItem, YearMonth


@dataclass(frozen=True)
class TotalRelevantExperience:
    years: Decimal
    contributing_item_ids: tuple[str, ...]


def _month_index(value: YearMonth) -> int:
    return value.year * 12 + value.month - 1


def total_relevant_experience(
    experience: Iterable[ExperienceItem],
    session_start_date: date,
) -> TotalRelevantExperience:
    """Union all dated, at-least-one-month entries using month-granularity math."""

    session_end = YearMonth(year=session_start_date.year, month=session_start_date.month)
    admitted: list[tuple[int, int, str]] = []
    for item in sorted(experience, key=lambda entry: entry.item_id):
        if item.start_date is None or (item.end_date is None and not item.is_present):
            continue
        end_date = session_end if item.is_present else item.end_date
        if end_date is None:
            continue
        start_index, end_index = _month_index(item.start_date), _month_index(end_date)
        if end_index - start_index < 1:
            continue
        admitted.append((start_index, end_index, item.item_id))
    intervals = sorted((start, end) for start, end, _ in admitted)
    merged: list[tuple[int, int]] = []
    for start, interval_end in intervals:
        if merged and start <= merged[-1][1]:
            previous_start, previous_end = merged[-1]
            merged[-1] = (previous_start, max(previous_end, interval_end))
        else:
            merged.append((start, interval_end))
    months = sum(end - start for start, end in merged)
    years = (Decimal(months) / Decimal(12)).quantize(Decimal("0.1"), rounding=ROUND_DOWN)
    return TotalRelevantExperience(years, tuple(sorted(item_id for _, _, item_id in admitted)))
