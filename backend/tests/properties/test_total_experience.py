from datetime import date
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from resumematch.core.schemas.candidate import ExperienceItem, YearMonth
from resumematch.matching.experience import total_relevant_experience


def _experience(item_id: str, start: tuple[int, int], end: tuple[int, int]) -> ExperienceItem:
    return ExperienceItem(
        item_id=item_id,
        origin="user_provided",
        extraction_confidence=Decimal("1.00"),
        confidence_inputs=(),
        provenance=None,
        source_text="source",
        employer="Example",
        title="Engineer",
        start_date=YearMonth(year=start[0], month=start[1]),
        end_date=YearMonth(year=end[0], month=end[1]),
        is_present=False,
        duration_months=None,
        description=None,
        date_conflict=False,
    )


def test_total_experience_merges_overlap_and_records_sorted_contributors() -> None:
    result = total_relevant_experience(
        (_experience("b", (2020, 1), (2021, 1)), _experience("a", (2020, 1), (2021, 1))),
        date(2026, 1, 1),
    )
    assert result.years == Decimal("1.0")
    assert result.contributing_item_ids == ("a", "b")


def test_total_experience_truncates_month_union_to_one_decimal_year() -> None:
    seventeen_months = _experience("item", (2020, 1), (2021, 6))
    eighteen_months = _experience("item", (2020, 1), (2021, 7))
    assert total_relevant_experience((seventeen_months,), date(2026, 1, 1)).years == Decimal("1.4")
    assert total_relevant_experience((eighteen_months,), date(2026, 1, 1)).years == Decimal("1.5")


@given(st.permutations(("a", "b", "c")))
def test_total_experience_is_invariant_under_experience_order(order: tuple[str, ...]) -> None:
    source = {
        "a": _experience("a", (2020, 1), (2021, 1)),
        "b": _experience("b", (2020, 6), (2021, 6)),
        "c": _experience("c", (2022, 1), (2022, 7)),
    }
    result = total_relevant_experience((source[item_id] for item_id in order), date(2026, 1, 1))
    assert result.years == Decimal("1.9")
    assert result.contributing_item_ids == ("a", "b", "c")
