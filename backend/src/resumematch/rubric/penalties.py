"""Typed, raw-text-free rubric-penalty applicability."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from resumematch.core.schemas.candidate import CandidateProfile

SectionId = Literal[
    "skills",
    "experience",
    "education",
    "projects",
    "certifications",
    "achievements",
    "unclassified",
]


class SectionItemCount(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    section_id: SectionId
    count: int = Field(ge=0)


class PenaltyApplicabilityContext(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    section_item_counts: tuple[SectionItemCount, ...]
    total_relevant_experience_months: int | None = Field(default=None, ge=0)
    context_version: Literal["penalty_applicability@1"]

    @field_validator("section_item_counts")
    @classmethod
    def requires_every_section(
        cls, values: tuple[SectionItemCount, ...]
    ) -> tuple[SectionItemCount, ...]:
        expected = {
            "skills",
            "experience",
            "education",
            "projects",
            "certifications",
            "achievements",
            "unclassified",
        }
        if {item.section_id for item in values} != expected:
            raise ValueError("section_item_counts must contain every closed section exactly once")
        if len(values) != len(expected):
            raise ValueError("section_item_counts must not duplicate sections")
        return values


def no_item_in_section(context: PenaltyApplicabilityContext, section_id: SectionId) -> bool:
    return (
        next(item.count for item in context.section_item_counts if item.section_id == section_id)
        == 0
    )


def total_experience_below(context: PenaltyApplicabilityContext, threshold_months: int) -> bool:
    if threshold_months < 0:
        raise ValueError("threshold_months must be non-negative")
    months = context.total_relevant_experience_months
    return months is not None and months < threshold_months


def applicability_context(
    profile: CandidateProfile, total_relevant_experience_months: int | None
) -> PenaltyApplicabilityContext:
    """Derive penalty facts from structured sections only."""

    resume = profile.resume
    counts = (
        SectionItemCount(section_id="skills", count=len(resume.skills)),
        SectionItemCount(section_id="experience", count=len(resume.experience)),
        SectionItemCount(section_id="education", count=len(resume.education)),
        SectionItemCount(section_id="projects", count=len(resume.projects)),
        SectionItemCount(section_id="certifications", count=len(resume.certifications)),
        SectionItemCount(section_id="achievements", count=len(resume.achievements)),
        SectionItemCount(section_id="unclassified", count=len(resume.unclassified)),
    )
    return PenaltyApplicabilityContext(
        section_item_counts=counts,
        total_relevant_experience_months=total_relevant_experience_months,
        context_version="penalty_applicability@1",
    )
