"""Canonical skill resolution without raw-text access."""

from resumematch.core.schemas.rubric import Signal
from resumematch.rubric.resolvers._common import expected, indeterminate, resolved
from resumematch.rubric.resolvers.context import ScoringContext
from resumematch.rubric.resolvers.contracts import ResolvedSignal


class SkillSignalResolver:
    signal_type = "skill"

    def resolve(self, signal: Signal, context: ScoringContext) -> ResolvedSignal:
        if not expected(signal, context.expected_targets):
            return indeterminate()
        matches = tuple(
            item for item in context.skills if item.canonical_skill_id == signal.target.target_id
        )
        level = (
            context.resolver_config.evidence_levels.skill["canonical_skill_match"] if matches else 0
        )
        return resolved(
            level,
            (item.item_id for item in matches),
            (item.extraction_confidence for item in matches),
            context.candidate_confirmed,
        )
