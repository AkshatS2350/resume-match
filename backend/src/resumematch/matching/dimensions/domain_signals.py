"""Normalized domain-signal scoring from configured public mappings."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from resumematch.core.schemas.candidate import CandidateProfile
from resumematch.core.schemas.job import JobPosting
from resumematch.job.normalizer import company_fold
from resumematch.matching.candidate_context import (
    CandidateContextResolver,
    resolve_candidate_context,
)
from resumematch.matching.contracts import DimensionId, DimensionScore, EvidenceIndex, MatchConfig

_UNKNOWN = "unknown"


class DomainSignalsDimensionScorer:
    """Choose the strongest configured candidate-domain to posting-domain score."""

    dimension_id = DimensionId.DOMAIN_SIGNALS

    def __init__(
        self, domain_table: Mapping[str, object], resolver: CandidateContextResolver
    ) -> None:
        self._by_company_fold = domain_table.get("by_company_fold")
        self._by_role_family_fallback = domain_table.get("by_role_family_fallback")
        self._pair_scores = domain_table.get("pair_scores")
        self._resolver = resolver

    def score(
        self,
        profile: CandidateProfile,
        posting: JobPosting,
        evidence: EvidenceIndex,
        config: MatchConfig,
    ) -> DimensionScore:
        del evidence
        context = resolve_candidate_context(profile, self._resolver)
        posting_domain = _posting_domain(
            posting, self._by_company_fold, self._by_role_family_fallback
        )
        candidate_domains = (context.target_domain, *context.employer_domains)
        raw_score = max(
            (
                _pair_score(self._pair_scores, candidate_domain, posting_domain)
                for candidate_domain in sorted(set(candidate_domains))
            ),
            default=Decimal("0"),
        )
        score = raw_score / Decimal("100")
        weight = config.dimension_weights[self.dimension_id]
        return DimensionScore(
            dimension_id=self.dimension_id,
            enabled=True,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            evidence_level=None,
            reason="configured_domain_pair" if raw_score else "unresolved_domain",
        )


def _posting_domain(
    posting: JobPosting, by_company_fold: object, by_role_family_fallback: object
) -> str:
    if isinstance(by_company_fold, dict):
        mapped = by_company_fold.get(company_fold(posting.company))
        if isinstance(mapped, str):
            return mapped
    if isinstance(by_role_family_fallback, dict) and posting.role_family is not None:
        fallback = by_role_family_fallback.get(posting.role_family)
        if isinstance(fallback, str):
            return fallback
    return _UNKNOWN


def _pair_score(pair_scores: object, candidate_domain: str, posting_domain: str) -> Decimal:
    if not isinstance(pair_scores, dict):
        return Decimal("0")
    row = pair_scores.get(candidate_domain)
    if not isinstance(row, dict):
        return Decimal("0")
    score = row.get(posting_domain)
    return Decimal(score) if isinstance(score, int) else Decimal("0")
