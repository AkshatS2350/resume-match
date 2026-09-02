from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from resumematch.rubric.arithmetic import clamp, quantize_half_up, sum_sorted


def test_quantize_half_up_is_not_bankers_rounding() -> None:
    assert quantize_half_up(Decimal("2.5")) == Decimal("3")
    assert quantize_half_up(Decimal("3.5")) == Decimal("4")


def test_clamp_honours_both_bounds() -> None:
    assert clamp(Decimal("-1"), Decimal("0"), Decimal("100")) == Decimal("0")
    assert clamp(Decimal("101"), Decimal("0"), Decimal("100")) == Decimal("100")


# Feature: resumematch, Property 15: scored arithmetic is order independent.
@given(st.lists(st.tuples(st.text(min_size=1), st.integers(-1000, 1000)), max_size=30))
def test_sum_sorted_is_permutation_invariant(values: list[tuple[str, int]]) -> None:
    pairs = [(identifier, Decimal(value)) for identifier, value in values]
    assert sum_sorted(pairs) == sum_sorted(list(reversed(pairs)))
