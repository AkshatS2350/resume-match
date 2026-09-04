"""Configured role-family and domain dimension scorer tests."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from resumematch.core.schemas.candidate import (
    CandidateProfile,
    ExperienceItem,
    Provenance,
    StructuredResume,
    TargetConstraints,
)
from resumematch.core.schemas.job import JobPosting
from resumematch.matching.candidate_context import load_candidate_context_resolver
from resumematch.matching.config import load_equivalence_table, load_match_config
from resumematch.matching.contracts import EvidenceIndex
from resumematch.matching.dimensions.domain_signals import DomainSignalsDimensionScorer
from resumematch.matching.dimensions.role_similarity import RoleSimilarityDimensionScorer

_ROOT = Path(__file__).parents[4]
_MATCH_CONFIG = load_match_config(
    _ROOT / "config" / "matching_contract.yaml", _ROOT / "config" / "match_weights.yaml"
)
_RESOLVER = load_candidate_context_resolver(_ROOT / "config" / "candidate_context_resolver.yaml")
_ROLE_TABLE = load_equivalence_table(
    _ROOT / "config" / "role_family_equivalence.yaml", "role_family_equivalence@1"
)
_DOMAIN_TABLE = load_equivalence_table(
    _ROOT / "config" / "company_domain_mapping.yaml", "company_domain_mapping@1"
)
_EVIDENCE = EvidenceIndex(evidence_index_version="evidence_index@1")


def _profile(
    *, role_id: str, domain_id: str, employer: str = "Unknown Organization"
) -> CandidateProfile:
    experience = ExperienceItem(
        item_id="experience-1",
        origin="extracted",
        extraction_confidence=Decimal("1.00"),
        confidence_inputs=(),
        provenance=Provenance(
            section_id="experience", block_ids=("block-1",), start_offset=0, end_offset=1
        ),
        source_text="experience",
        employer=employer,
        title=None,
        start_date=None,
        end_date=None,
        is_present=False,
        duration_months=None,
        description=None,
        date_conflict=False,
    )
    return CandidateProfile(
        schema_version="candidate_profile/1",
        profile_revision=1,
        session_start_date=date(2026, 1, 1),
        resume=StructuredResume(
            schema_version="structured_resume/1",
            summary=None,
            skills=(),
            experience=(experience,),
            education=(),
            projects=(),
            certifications=(),
            achievements=(),
            unclassified=(),
        ),
        target=TargetConstraints(
            domain_id=domain_id,
            role_id=role_id,
            seniority_id="entry",
            locations=(),
            work_modes=(),
        ),
        confirmed=True,
    )


def _posting(*, company: str, role_family: str) -> JobPosting:
    return JobPosting(
        schema_version="job_posting/1",
        internal_id="posting-1",
        source_id="fixture",
        source_external_id="posting-1",
        company=company,
        raw_title="Engineer",
        raw_description="",
        apply_url="https://example.invalid/jobs/posting-1",
        role_family=role_family,
        ingested_at=datetime(2026, 1, 1),
    )


def test_absent_ordered_pairs_score_zero() -> None:
    scorer = RoleSimilarityDimensionScorer(_ROLE_TABLE, _RESOLVER)

    score = scorer.score(
        _profile(role_id="backend_engineer", domain_id="software_engineering"),
        _posting(company="Example", role_family="unlisted"),
        _EVIDENCE,
        _MATCH_CONFIG,
    )

    assert score.score == Decimal("0")


def test_embedded_and_software_pairs_preserve_configured_asymmetry() -> None:
    scorer = RoleSimilarityDimensionScorer(_ROLE_TABLE, _RESOLVER)
    embedded_to_software = scorer.score(
        _profile(role_id="embedded_firmware_engineer", domain_id="embedded_firmware"),
        _posting(company="Example", role_family="software_engineering"),
        _EVIDENCE,
        _MATCH_CONFIG,
    )
    software_to_embedded = scorer.score(
        _profile(role_id="backend_engineer", domain_id="software_engineering"),
        _posting(company="Example", role_family="embedded_firmware"),
        _EVIDENCE,
        _MATCH_CONFIG,
    )

    assert embedded_to_software.score == Decimal("0.70")
    assert software_to_embedded.score == Decimal("0.65")


def test_unlisted_company_uses_role_family_domain_fallback() -> None:
    scorer = DomainSignalsDimensionScorer(_DOMAIN_TABLE, _RESOLVER)

    score = scorer.score(
        _profile(role_id="financial_analyst", domain_id="finance"),
        _posting(company="Unlisted Organization", role_family="finance"),
        _EVIDENCE,
        _MATCH_CONFIG,
    )

    assert score.score == Decimal("1")
