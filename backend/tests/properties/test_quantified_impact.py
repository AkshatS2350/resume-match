from hypothesis import given
from hypothesis import strategies as st

from resumematch.rubric.quantity import find_quantified_impacts, quantified_impact

_UNITS = frozenset({"%", "orders"})


def test_quantified_impact_applies_only_to_permitted_numeric_expressions() -> None:
    assert quantified_impact("item-1", "reduced cost by 40%", _UNITS)
    assert quantified_impact("item-1", "handled 12 000 orders", _UNITS)
    assert not quantified_impact("item-1", "Python 3.11", _UNITS)
    assert not quantified_impact("item-1", "graduated 2019", _UNITS)
    assert not quantified_impact("item-1", "Jan 2020", _UNITS, date_field_values=("2020",))


def test_quantified_impact_reports_an_exclusive_source_range() -> None:
    text = "reduced cost by 40%"
    match = find_quantified_impacts("item-1", text, frozenset({"%"}))[0]
    assert match.item_id == "item-1"
    assert text[match.start_offset : match.end_offset] == "40%"


@given(st.integers(min_value=0, max_value=1899), st.sampled_from(("%", "orders")))
def test_quantity_rule_is_true_for_non_date_configured_expressions(number: int, unit: str) -> None:
    assert quantified_impact("item", f"improved result by {number}{unit}", _UNITS)
