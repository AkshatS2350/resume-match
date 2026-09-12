"""Test-only candidate marker strategy and containment assertion."""

from __future__ import annotations

import string
from datetime import date
from decimal import Decimal

from hypothesis import strategies as st

from resumematch.core.schemas.candidate import (
    AchievementItem,
    CandidateProfile,
    CertificationItem,
    EducationItem,
    ExperienceItem,
    ProjectItem,
    Provenance,
    SeniorityId,
    SkillItem,
    StructuredResume,
    TargetConstraints,
    UnclassifiedItem,
)

_MARKER_ALPHABET = string.ascii_lowercase + string.digits
_MARKER_COUNT = 73


@st.composite
def marker_profiles(
    draw: st.DrawFn,
) -> tuple[CandidateProfile, frozenset[str]]:
    """Seed an independent high-entropy marker into every candidate text field."""

    suffixes = draw(
        st.lists(
            st.text(alphabet=_MARKER_ALPHABET, min_size=32, max_size=32),
            min_size=_MARKER_COUNT,
            max_size=_MARKER_COUNT,
            unique=True,
        )
    )
    markers = tuple(f"candidate-marker-{suffix}" for suffix in suffixes)
    marker = iter(markers)
    def base() -> dict[str, object]:
        return {
            "item_id": next(marker),
            "origin": "extracted",
            "extraction_confidence": Decimal("0.75"),
            "confidence_inputs": (next(marker),),
            "provenance": Provenance(
                section_id=next(marker),
                block_ids=(next(marker),),
                start_offset=0,
                end_offset=1,
            ),
            "source_text": next(marker),
        }
    profile = CandidateProfile(
        schema_version="candidate_profile/1",
        profile_revision=0,
        session_start_date=date(2026, 9, 10),
        resume=StructuredResume(
            schema_version="structured_resume/1",
            summary=next(marker),
            skills=(SkillItem(**base(), surface=next(marker), canonical_skill_id=next(marker)),),
            experience=(
                ExperienceItem(
                    **base(),
                    employer=next(marker),
                    title=next(marker),
                    start_date=None,
                    end_date=None,
                    is_present=False,
                    duration_months=None,
                    description=next(marker),
                    date_conflict=False,
                ),
            ),
            education=(
                EducationItem(
                    **base(),
                    institution=next(marker),
                    degree_level=None,
                    field_of_study=next(marker),
                    start_date=None,
                    end_date=None,
                    coursework=(next(marker),),
                ),
            ),
            projects=(ProjectItem(**base(), name=next(marker), description=next(marker)),),
            certifications=(
                CertificationItem(
                    **base(),
                    name=next(marker),
                    canonical_certification_id=next(marker),
                    issuer=next(marker),
                    issued=None,
                ),
            ),
            achievements=(AchievementItem(**base(), text=next(marker)),),
            unclassified=(UnclassifiedItem(**base(), text=next(marker)),),
        ),
        target=TargetConstraints(
            domain_id=next(marker),
            role_id=next(marker),
            seniority_id=SeniorityId.ENTRY,
            locations=(next(marker),),
            work_modes=(),
        ),
        confirmed=True,
    )
    return profile, frozenset(markers)


def assert_markers_absent(markers: frozenset[str], values: tuple[str, ...]) -> None:
    """Fail with no marker value in the failure message itself."""

    for marker in markers:
        assert all(marker not in value for value in values), "candidate marker leaked"
