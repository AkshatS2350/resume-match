"""Deterministic, provider-free Role_Rubric scoring loop."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Literal, cast

from resumematch.core.errors import PipelineError, ScoringFailedError
from resumematch.core.schemas.candidate import CandidateProfile
from resumematch.core.schemas.rubric import RoleRubric, RubricPenalty, Signal
from resumematch.core.schemas.version_stamp import VersionStamp
from resumematch.core.telemetry import emit_metric
from resumematch.rubric.arithmetic import clamp, quantize_half_up, sum_sorted
from resumematch.rubric.evidence import EvidenceAssigner
from resumematch.rubric.penalties import (
    PenaltyApplicabilityContext,
    applicability_context,
    no_item_in_section,
    total_experience_below,
)
from resumematch.rubric.resolver_config import SignalResolverConfig
from resumematch.rubric.resolvers import RESOLVERS, ResolvedSignal, SignalResolver
from resumematch.rubric.resolvers.context import ScoringContext, scoring_context_from_profile


@dataclass(frozen=True)
class CategoryScore:
    category_id: str
    score: int
    matched_signal_ids: tuple[str, ...]
    applied_penalty_ids: tuple[str, ...]
    alternative_credits: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class RubricScore:
    score: int
    reason: Literal["scored", "no_evidence", "below_reportable_or_penalized"]
    matched_signal_count: int
    categories: tuple[CategoryScore, ...]
    versions: VersionStamp


class RubricEngine:
    """Score only declarative rubric data and structured resolver facts."""

    engine_version: ClassVar[str] = "rubric_engine@1"

    def score_profile(
        self,
        profile: CandidateProfile,
        rubric: RoleRubric,
        resolver_config: SignalResolverConfig,
        config_versions: VersionStamp,
        multipliers: dict[int, Decimal],
        *,
        total_relevant_experience_months: int | None,
    ) -> RubricScore:
        """Build the approved scoring boundary then run the one generic engine path."""

        required_skill_ids = frozenset(
            signal.target.target_id
            for category in rubric.categories
            for signal in category.signals
            if signal.type == "skill"
        )
        evidence_assignments = EvidenceAssigner().assign(
            profile, required_skill_ids, profile.session_start_date
        )
        context = scoring_context_from_profile(
            profile, rubric, resolver_config, config_versions, evidence_assignments
        )
        return self.score(
            rubric,
            context,
            multipliers,
            applicability_context(profile, total_relevant_experience_months),
        )

    def score(
        self,
        rubric: RoleRubric,
        context: ScoringContext,
        multipliers: dict[int, Decimal],
        penalty_context: PenaltyApplicabilityContext,
    ) -> RubricScore:
        maximum_multiplier = max(value for _, value in sorted(multipliers.items()))
        category_scores: list[CategoryScore] = []
        weighted: list[tuple[str, Decimal]] = []
        for category in sorted(rubric.categories, key=lambda value: value.category_id):
            resolved_items: list[tuple[Signal, ResolvedSignal]] = []
            for signal in sorted(category.signals, key=lambda value: value.signal_id):
                try:
                    result = cast(SignalResolver, RESOLVERS[signal.type]).resolve(signal, context)
                except PipelineError:
                    raise
                except Exception as error:
                    emit_metric(
                        "scoring_exception_total",
                        rubric_id=rubric.rubric_id,
                        engine_version=self.engine_version,
                    )
                    raise ScoringFailedError("Scoring failed. Please try again.") from error
                resolved_items.append((signal, result))
            resolved = tuple(resolved_items)
            earned = sum_sorted(
                (
                    signal.signal_id,
                    signal.weight * multipliers[result.evidence_level]
                    if result.evidence_level >= signal.min_evidence_level
                    else Decimal("0"),
                )
                for signal, result in resolved
            )
            attainable = sum_sorted(
                (signal.signal_id, signal.weight * maximum_multiplier) for signal, _ in resolved
            )
            resolved_by_id = {signal.signal_id: result for signal, result in resolved}
            alternative_credits: list[tuple[str, str]] = []
            for group in sorted(category.alternative_groups, key=lambda value: value.group_id):
                qualifying = tuple(
                    member
                    for member in sorted(group.members)
                    if member in resolved_by_id
                    and resolved_by_id[member].evidence_level >= group.min_evidence_level
                )
                attainable += group.weight * maximum_multiplier
                if qualifying:
                    highest_level = max(
                        resolved_by_id[identifier].evidence_level for identifier in qualifying
                    )
                    credited = min(
                        identifier
                        for identifier in qualifying
                        if resolved_by_id[identifier].evidence_level == highest_level
                    )
                    earned += group.weight * multipliers[resolved_by_id[credited].evidence_level]
                    alternative_credits.append((group.group_id, credited))
            raw = Decimal("0") if attainable == 0 else Decimal("100") * earned / attainable
            penalties = tuple(
                penalty
                for penalty in sorted(rubric.penalties, key=lambda value: value.penalty_id)
                if penalty.applies_to_category == category.category_id
                and _applies(penalty, resolved, penalty_context)
            )
            adjusted = clamp(
                raw - sum_sorted((penalty.penalty_id, penalty.points) for penalty in penalties),
                Decimal("0"),
                Decimal("100"),
            )
            reported = int(quantize_half_up(adjusted))
            category_scores.append(
                CategoryScore(
                    category.category_id,
                    reported,
                    tuple(
                        signal.signal_id for signal, result in resolved if result.evidence_level > 0
                    ),
                    tuple(penalty.penalty_id for penalty in penalties),
                    tuple(alternative_credits),
                )
            )
            weighted.append(
                (category.category_id, Decimal(reported) * category.weight / Decimal("100"))
            )
        overall = int(quantize_half_up(clamp(sum_sorted(weighted), Decimal("0"), Decimal("100"))))
        matched_signal_count = sum(len(category.matched_signal_ids) for category in category_scores)
        reason: Literal["scored", "no_evidence", "below_reportable_or_penalized"] = "scored"
        if matched_signal_count == 0:
            reason = "no_evidence"
        elif overall == 0:
            reason = "below_reportable_or_penalized"
        versions = context.config_versions.model_copy(
            update={
                "engine_version": self.engine_version,
                "rubric_id": rubric.rubric_id,
                "rubric_version": rubric.rubric_version,
                "rubric_status": rubric.status,
            }
        )
        return RubricScore(overall, reason, matched_signal_count, tuple(category_scores), versions)


def _applies(
    penalty: RubricPenalty,
    resolved: tuple[tuple[Signal, ResolvedSignal], ...],
    context: PenaltyApplicabilityContext,
) -> bool:
    kind = penalty.condition.kind
    if kind == "no_item_in_section":
        assert penalty.condition.section is not None
        return no_item_in_section(context, penalty.condition.section)
    if kind == "total_experience_below":
        assert penalty.condition.threshold_months is not None
        return total_experience_below(context, penalty.condition.threshold_months)
    levels = tuple(result.evidence_level for _, result in resolved)
    if kind == "all_signals_absent_in_category":
        return not any(level > 0 for level in levels)
    return any(
        result.evidence_level < signal.min_evidence_level for signal, result in resolved
    )
