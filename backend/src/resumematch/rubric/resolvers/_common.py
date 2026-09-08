"""Shared deterministic resolver decisions."""

from collections.abc import Iterable
from decimal import Decimal

from resumematch.core.schemas.rubric import Signal, SignalTargetRef
from resumematch.rubric.resolvers.contracts import ResolvedSignal


def expected(signal: Signal, targets: tuple[SignalTargetRef, ...]) -> bool:
    return signal.target in targets


def resolved(
    level: int, item_ids: Iterable[str], confidences: Iterable[Decimal], confirmed: bool
) -> ResolvedSignal:
    ids = tuple(sorted(item_ids))
    confidence_values = tuple(confidences)
    determinate = not (
        len(ids) == 1
        and len(confidence_values) == 1
        and confidence_values[0] < Decimal("0.60")
        and not confirmed
    )
    return ResolvedSignal(level, "determinable" if determinate else "indeterminate", ids)


def indeterminate() -> ResolvedSignal:
    return ResolvedSignal(0, "indeterminate", ())
