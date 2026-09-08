"""Configured certification resolution without raw-text access."""

from resumematch.core.schemas.rubric import Signal
from resumematch.rubric.resolvers._common import expected, indeterminate, resolved
from resumematch.rubric.resolvers.context import ScoringContext
from resumematch.rubric.resolvers.contracts import ResolvedSignal


class CertificationResolver:
    signal_type = "certification"

    def resolve(self, signal: Signal, context: ScoringContext) -> ResolvedSignal:
        if not expected(signal, context.expected_targets):
            return indeterminate()
        target = next(
            (
                value
                for value in context.resolver_config.certification_targets
                if value.certification_id == signal.target.target_id
            ),
            None,
        )
        if target is None or any(
            item.canonical_certification_id is None for item in context.certifications
        ):
            return indeterminate()
        exact = tuple(
            item
            for item in context.certifications
            if item.canonical_certification_id == target.certification_id
        )
        equivalent = tuple(
            item
            for item in context.certifications
            if item.canonical_certification_id in target.equivalent_certification_ids
        )
        matches = exact or equivalent
        level = (
            context.resolver_config.evidence_levels.certification[
                "exact_configured_certification_match"
            ]
            if exact
            else context.resolver_config.evidence_levels.certification[
                "configured_equivalent_certification_match"
            ]
            if equivalent
            else 0
        )
        return resolved(
            level,
            (item.item_id for item in matches),
            (item.extraction_confidence for item in matches),
            context.candidate_confirmed,
        )
