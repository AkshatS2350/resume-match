"""Tests for deterministic, config-backed candidate matching context."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from resumematch.core.schemas.candidate import (
    CandidateProfile,
    ExperienceItem,
    Provenance,
    StructuredResume,
    TargetConstraints,
)
from resumematch.matching.candidate_context import (
    load_candidate_context_resolver,
    resolve_candidate_context,
)

_CONFIG = Path(__file__).parents[4] / "config" / "candidate_context_resolver.yaml"


def _profile(*, role_id: str, domain_id: str, title: str, employer: str) -> CandidateProfile:
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
        title=title,
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


def test_configured_candidate_context_resolves_exact_mappings() -> None:
    resolver = load_candidate_context_resolver(_CONFIG)

    context = resolve_candidate_context(
        _profile(
            role_id="backend_engineer",
            domain_id="software_engineering",
            title="Backend Engineer",
            employer="Northwind Systems, Inc.",
        ),
        resolver,
    )

    assert context.resolver_version == "candidate_context_resolver@1"
    assert context.target_role_family == "software_engineering"
    assert context.prior_role_families == ("software_engineering",)
    assert context.target_domain == "software_saas"
    assert context.employer_domains == ("software_saas",)


def test_unknown_candidate_context_stays_unknown_without_inference() -> None:
    resolver = load_candidate_context_resolver(_CONFIG)

    context = resolve_candidate_context(
        _profile(
            role_id="unlisted_role",
            domain_id="unlisted_domain",
            title="Chief Wizard",
            employer="Mystery Holdings",
        ),
        resolver,
    )

    assert context.target_role_family == "unknown"
    assert context.prior_role_families == ()
    assert context.target_domain == "unknown"
    assert context.employer_domains == ()


def test_configured_phrase_and_token_resolution_are_deterministic() -> None:
    resolver = load_candidate_context_resolver(_CONFIG)
    profile = _profile(
        role_id="financial_analyst",
        domain_id="finance",
        title="Equity Research Analyst",
        employer="Acme Capital Management",
    )

    first = resolve_candidate_context(profile, resolver)
    second = resolve_candidate_context(profile, resolver)

    assert first == second
    assert first.prior_role_families == ("finance",)
    assert first.employer_domains == ("financial_services",)
