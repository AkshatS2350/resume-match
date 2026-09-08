"""Configured education resolution without raw-text access."""

from resumematch.core.schemas.candidate import DegreeLevel
from resumematch.core.schemas.rubric import Signal
from resumematch.rubric.resolver_config import EducationTarget
from resumematch.rubric.resolvers._common import expected, indeterminate, resolved
from resumematch.rubric.resolvers.context import EducationEvidence, ScoringContext
from resumematch.rubric.resolvers.contracts import ResolvedSignal

_RANK = {
    DegreeLevel.NONE: 0,
    DegreeLevel.ASSOCIATE: 1,
    DegreeLevel.BACHELORS: 2,
    DegreeLevel.MASTERS: 3,
    DegreeLevel.DOCTORATE: 4,
}


class EducationResolver:
    signal_type = "education"

    def resolve(self, signal: Signal, context: ScoringContext) -> ResolvedSignal:
        if not expected(signal, context.expected_targets):
            return indeterminate()
        target = next(
            (
                value
                for value in context.resolver_config.education_targets
                if value.target_id == signal.target.target_id
            ),
            None,
        )
        if target is None or any(item.degree_level is None for item in context.education):
            return indeterminate()
        matches = tuple(
            item
            for item in context.education
            if item.degree_level is not None
            and _RANK[item.degree_level] >= _RANK[target.min_degree_level]
        )
        levels = tuple(_level(item, target, context) for item in matches)
        level = max(levels, default=0)
        supports = tuple(item for item in matches if _level(item, target, context) == level)
        return resolved(
            level,
            (item.item_id for item in supports),
            (item.extraction_confidence for item in supports),
            context.candidate_confirmed,
        )


def _level(item: EducationEvidence, target: EducationTarget, context: ScoringContext) -> int:
    levels = context.resolver_config.evidence_levels.education
    if item.field_id is not None and item.field_id in target.exact_field_ids:
        return levels["exact_or_higher_degree_and_exact_field"]
    if item.field_id is not None and item.field_id in target.related_field_ids:
        return levels["exact_or_higher_degree_related_field"]
    return levels["degree_only_match"] if not target.field_required else 0
