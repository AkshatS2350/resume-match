"""Closed structured-flag resolution without raw-text access."""

from resumematch.core.schemas.rubric import Signal
from resumematch.rubric.resolvers._common import expected, indeterminate, resolved
from resumematch.rubric.resolvers.context import ScoringContext
from resumematch.rubric.resolvers.contracts import ResolvedSignal


class FlagResolver:
    signal_type = "flag"

    def resolve(self, signal: Signal, context: ScoringContext) -> ResolvedSignal:
        if (
            not expected(signal, context.expected_targets)
            or signal.target.target_id not in context.resolver_config.closed_flags
        ):
            return indeterminate()
        matches = tuple(
            item for item in context.flags if item.flag_id == signal.target.target_id and item.value
        )
        level = (
            context.resolver_config.evidence_levels.closed_flag["quantified_impact"][
                "explicit_structured_flag_true"
            ]
            if matches
            else 0
        )
        return resolved(
            level,
            (item.item_id for item in matches),
            (item.extraction_confidence for item in matches),
            context.candidate_confirmed,
        )
