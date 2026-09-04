"""Conversion of normalized matching values at the reporting boundary."""

from decimal import Decimal

from resumematch.rubric.arithmetic import quantize_half_up


def reported_dimension_score(normalized_score: Decimal | None) -> int | None:
    """Render a normalized internal score as the public integral 0–100 value."""

    if normalized_score is None:
        return None
    return int(quantize_half_up(normalized_score * Decimal("100")))
