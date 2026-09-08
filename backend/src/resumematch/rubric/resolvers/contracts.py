"""Closed resolver contracts."""

from dataclasses import dataclass
from typing import Literal, Protocol

from resumematch.core.schemas.rubric import Signal
from resumematch.rubric.resolvers.context import ScoringContext

SignalType = Literal["skill", "experience_band", "education", "certification", "flag"]
Determinability = Literal["determinable", "indeterminate"]


@dataclass(frozen=True)
class ResolvedSignal:
    evidence_level: int
    determinability: Determinability
    supporting_item_ids: tuple[str, ...]


class SignalResolver(Protocol):
    signal_type: SignalType

    def resolve(self, signal: Signal, context: ScoringContext) -> ResolvedSignal: ...
