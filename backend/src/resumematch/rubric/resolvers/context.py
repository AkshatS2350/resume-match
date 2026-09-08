"""Raw-text-free resolver inputs assembled by the scoring boundary."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from resumematch.core.schemas.candidate import CandidateProfile, DegreeLevel
from resumematch.core.schemas.rubric import RoleRubric, SignalTargetRef
from resumematch.core.schemas.version_stamp import VersionStamp
from resumematch.rubric.evidence import EvidenceAssignment
from resumematch.rubric.resolver_config import SignalResolverConfig


class SkillEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    canonical_skill_id: str
    item_id: str
    extraction_confidence: Decimal


class ExperienceEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    item_id: str
    extraction_confidence: Decimal
    total_months: int | None


class EducationEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    item_id: str
    extraction_confidence: Decimal
    degree_level: DegreeLevel | None
    field_id: str | None


class CertificationEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    item_id: str
    extraction_confidence: Decimal
    canonical_certification_id: str | None


class ClosedFlagEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    flag_id: str
    item_id: str
    value: bool
    extraction_confidence: Decimal


class ScoringContext(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    rubric_id: str
    rubric_version: str
    target_domain_id: str
    target_role_id: str
    expected_targets: tuple[SignalTargetRef, ...]
    config_versions: VersionStamp
    candidate_confirmed: bool
    resolver_config: SignalResolverConfig
    skills: tuple[SkillEvidence, ...]
    experience: tuple[ExperienceEvidence, ...]
    education: tuple[EducationEvidence, ...]
    certifications: tuple[CertificationEvidence, ...]
    flags: tuple[ClosedFlagEvidence, ...]


def scoring_context_from_profile(
    profile: CandidateProfile,
    rubric: RoleRubric,
    resolver_config: SignalResolverConfig,
    config_versions: VersionStamp,
    evidence_assignments: tuple[EvidenceAssignment, ...] = (),
) -> ScoringContext:
    """Project approved structured profile facts into the raw-text-free resolver boundary."""

    resume = profile.resume
    evidence_by_id = {
        assignment.determining_item_id: assignment
        for assignment in sorted(evidence_assignments, key=lambda value: value.canonical_skill_id)
        if assignment.determining_item_id is not None and assignment.quantified_impact
    }
    expected_targets = tuple(
        signal.target
        for category in sorted(rubric.categories, key=lambda value: value.category_id)
        for signal in sorted(category.signals, key=lambda value: value.signal_id)
    )
    return ScoringContext(
        rubric_id=rubric.rubric_id,
        rubric_version=rubric.rubric_version,
        target_domain_id=rubric.domain_id,
        target_role_id=rubric.role_id,
        expected_targets=expected_targets,
        config_versions=config_versions,
        candidate_confirmed=profile.confirmed,
        resolver_config=resolver_config,
        skills=tuple(
            SkillEvidence(
                canonical_skill_id=item.canonical_skill_id,
                item_id=item.item_id,
                extraction_confidence=item.extraction_confidence,
            )
            for item in sorted(resume.skills, key=lambda value: value.item_id)
        ),
        experience=tuple(
            ExperienceEvidence(
                item_id=item.item_id,
                extraction_confidence=item.extraction_confidence,
                total_months=item.duration_months,
            )
            for item in sorted(resume.experience, key=lambda value: value.item_id)
        ),
        education=tuple(
            EducationEvidence(
                item_id=item.item_id,
                extraction_confidence=item.extraction_confidence,
                degree_level=item.degree_level,
                field_id=None,
            )
            for item in sorted(resume.education, key=lambda value: value.item_id)
        ),
        certifications=tuple(
            CertificationEvidence(
                item_id=item.item_id,
                extraction_confidence=item.extraction_confidence,
                canonical_certification_id=item.canonical_certification_id,
            )
            for item in sorted(resume.certifications, key=lambda value: value.item_id)
        ),
        flags=tuple(
            ClosedFlagEvidence(
                flag_id="quantified_impact",
                item_id=item_id,
                value=True,
                extraction_confidence=Decimal("1.00"),
            )
            for item_id, _ in sorted(evidence_by_id.items())
        ),
    )
