"""Deterministic per-item evidence-level assignment."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from resumematch.core.schemas.candidate import (
    CandidateProfile,
    ExperienceItem,
    ItemBase,
    ProjectItem,
    SkillItem,
)


@dataclass(frozen=True)
class ItemEvidence:
    level: int
    unmet_level3_condition: str | None
    demotion_reason: str | None


@dataclass(frozen=True)
class SupportingItem:
    item_id: str
    level: int


@dataclass(frozen=True)
class EvidenceAssignment:
    canonical_skill_id: str
    level: int
    quantified_impact: bool
    supporting_items: tuple[SupportingItem, ...]
    determining_item_id: str | None
    quantity_match: None = None
    demotion_reason: str | None = None
    unmet_level3_condition: str | None = None


@dataclass(frozen=True)
class EvidenceAssigner:
    """Assign a deterministic, maximal evidence level to each relevant skill."""

    def assign(
        self,
        profile: CandidateProfile,
        required_skill_ids: frozenset[str],
        session_start_date: date,
    ) -> tuple[EvidenceAssignment, ...]:
        items = tuple(
            sorted(
                (
                    *profile.resume.skills,
                    *profile.resume.experience,
                    *profile.resume.projects,
                    *profile.resume.education,
                    *profile.resume.certifications,
                    *profile.resume.achievements,
                    *profile.resume.unclassified,
                ),
                key=lambda item: item.item_id,
            )
        )
        profile_skills = {item.canonical_skill_id for item in profile.resume.skills}
        assignments: list[EvidenceAssignment] = []
        for skill_id in sorted(profile_skills | required_skill_ids):
            supporting = tuple(item for item in items if _supports(item, skill_id))
            per_item = tuple(
                (item, level_for_item(item, skill_id, session_start_date, len(supporting)))
                for item in supporting
            )
            if not per_item:
                assignments.append(EvidenceAssignment(skill_id, 0, False, (), None))
                continue
            item, evidence = max(per_item, key=lambda entry: (entry[1].level, entry[0].item_id))
            assignments.append(
                EvidenceAssignment(
                    skill_id,
                    evidence.level,
                    False,
                    tuple(SupportingItem(value.item_id, level.level) for value, level in per_item),
                    item.item_id,
                    demotion_reason=evidence.demotion_reason,
                    unmet_level3_condition=evidence.unmet_level3_condition,
                )
            )
        return tuple(assignments)


def _supports(item: ItemBase, skill_id: str) -> bool:
    if isinstance(item, SkillItem):
        return item.canonical_skill_id == skill_id
    return skill_id.casefold() in item.source_text.casefold()


def level_for_item(
    item: ItemBase,
    canonical_skill_id: str,
    session_start_date: date,
    distinct_skill_count: int,
) -> ItemEvidence:
    """Evaluate the fixed Level 3 conditions for an experience item."""

    if isinstance(item, ProjectItem):
        return ItemEvidence(2, None, None)
    if not isinstance(item, ExperienceItem):
        return ItemEvidence(1, None, None)
    if len("".join((item.employer or "").split())) < 2:
        return ItemEvidence(2, "employer", None)
    if item.start_date is None or (item.end_date is None and not item.is_present):
        return ItemEvidence(2, "dates", None)
    if item.is_present:
        end_year, end_month = session_start_date.year, session_start_date.month
    else:
        assert item.end_date is not None
        end_year, end_month = item.end_date.year, item.end_date.month
    resolved_months = (end_year - item.start_date.year) * 12 + end_month - item.start_date.month
    if item.duration_months is None or item.duration_months < 1 or resolved_months < 1:
        return ItemEvidence(2, "duration", None)
    text = " ".join(part for part in (item.title, item.description) if part)
    if canonical_skill_id.casefold() not in text.casefold():
        return ItemEvidence(2, "mention", None)
    if distinct_skill_count > 20:
        return ItemEvidence(2, None, "too_many_skills")
    return ItemEvidence(3, None, None)
