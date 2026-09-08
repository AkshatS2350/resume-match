"""Configured experience-band resolution without raw-text access."""

from resumematch.core.schemas.rubric import Signal
from resumematch.rubric.resolvers._common import expected, indeterminate, resolved
from resumematch.rubric.resolvers.context import ScoringContext
from resumematch.rubric.resolvers.contracts import ResolvedSignal


class ExperienceBandResolver:
    signal_type = "experience_band"

    def resolve(self, signal: Signal, context: ScoringContext) -> ResolvedSignal:
        if not expected(signal, context.expected_targets):
            return indeterminate()
        band = next(
            (
                value
                for value in context.resolver_config.experience_bands
                if value.band_id == signal.target.target_id
            ),
            None,
        )
        if band is None or any(item.total_months is None for item in context.experience):
            return indeterminate()
        matches = tuple(
            item
            for item in context.experience
            if item.total_months is not None
            and item.total_months >= band.min_months
            and (band.max_months is None or item.total_months <= band.max_months)
        )
        level = (
            context.resolver_config.evidence_levels.experience_band["exact_configured_band_match"]
            if matches
            else 0
        )
        return resolved(
            level,
            (item.item_id for item in matches),
            (item.extraction_confidence for item in matches),
            context.candidate_confirmed,
        )
