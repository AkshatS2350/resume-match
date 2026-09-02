"""Exact, order-stable arithmetic primitives used by rubric scoring."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Context, Decimal, localcontext

DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_UP)


def quantize_half_up(value: Decimal) -> Decimal:
    """Round a reported score to an integral Decimal using half-up semantics."""

    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def clamp(value: Decimal, lower: Decimal, upper: Decimal) -> Decimal:
    """Constrain ``value`` to an inclusive exact-Decimal interval."""

    return max(lower, min(value, upper))


def sum_sorted(pairs: Iterable[tuple[str, Decimal]]) -> Decimal:
    """Accumulate values by deterministic identifier order."""

    with localcontext(DECIMAL_CONTEXT):
        total = Decimal("0")
        for _, value in sorted(pairs, key=lambda pair: pair[0]):
            total += value
        return total
