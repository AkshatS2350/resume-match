"""Deterministic composition of extraction blocks into a structured resume."""

from datetime import date

from resumematch.core.schemas.candidate import (
    AchievementItem,
    CertificationItem,
    EducationItem,
    ExperienceItem,
    ProjectItem,
    Provenance,
    StructuredResume,
    UnclassifiedItem,
)
from resumematch.core.schemas.extracted_text import ExtractedBlock, ExtractedText
from resumematch.resume.structure.confidence import ExtractionConfidence, extraction_confidence
from resumematch.resume.structure.dates import parse_experience_dates
from resumematch.resume.structure.sections import SectionHeadings, assign_sections
from resumematch.resume.structure.skills import skill_item
from resumematch.skill.normalizer import SkillNormalizer


def structure(
    extracted: ExtractedText,
    session_start_date: date,
    headings: SectionHeadings,
    normalizer: SkillNormalizer,
) -> StructuredResume:
    """Structure each non-heading block exactly once without provider access."""

    assignments = assign_sections(extracted.blocks, headings)
    by_id = {block.block_id: block for block in extracted.blocks}
    blocks_by_section = {
        section_id: tuple(
            by_id[block_id] for block_id in block_ids if by_id[block_id].layout_kind != "heading"
        )
        for section_id, block_ids in assignments.items()
    }
    return StructuredResume(
        schema_version="structured_resume/1",
        summary=_summary(blocks_by_section["summary"]),
        skills=tuple(
            skill_item(
                item_id=f"skill:{block.block_id}",
                surface=block.text,
                normalizer=normalizer,
                confidence=_confidence(block, "skills").value,
                confidence_inputs=_confidence(block, "skills").inputs,
                provenance=_provenance(block, "skills"),
            )
            for block in blocks_by_section["skills"]
        ),
        experience=tuple(
            _experience(block, session_start_date) for block in blocks_by_section["experience"]
        ),
        education=tuple(_education(block) for block in blocks_by_section["education"]),
        projects=tuple(_project(block) for block in blocks_by_section["projects"]),
        certifications=tuple(
            _certification(block) for block in blocks_by_section["certifications"]
        ),
        achievements=tuple(_achievement(block) for block in blocks_by_section["achievements"]),
        unclassified=tuple(_unclassified(block) for block in blocks_by_section["unclassified"]),
    )


def _confidence(block: ExtractedBlock, section_id: str) -> ExtractionConfidence:
    return extraction_confidence(
        heading_matched=section_id != "unclassified",
        layout_clean=block.layout_kind != "text_box",
        pattern_complete=False,
        date_parsed=False,
        unclassified_section=section_id == "unclassified",
        encoding_anomaly=False,
        table_spliced=block.layout_kind == "table_cell",
    )


def _provenance(block: ExtractedBlock, section_id: str) -> Provenance:
    return Provenance(
        section_id=section_id,
        block_ids=(block.block_id,),
        start_offset=block.start_offset,
        end_offset=block.end_offset,
    )


def _summary(blocks: tuple[ExtractedBlock, ...]) -> str | None:
    return "\n".join(block.text for block in blocks) if blocks else None


def _experience(block: ExtractedBlock, session_start_date: date) -> ExperienceItem:
    dates = parse_experience_dates(block.text, session_start_date)
    confidence = _confidence(block, "experience")
    return ExperienceItem(
        item_id=f"experience:{block.block_id}",
        origin="extracted",
        extraction_confidence=confidence.value,
        confidence_inputs=confidence.inputs,
        provenance=_provenance(block, "experience"),
        source_text=block.text,
        employer=None,
        title=None,
        start_date=dates.start_date,
        end_date=dates.end_date,
        is_present=dates.is_present,
        duration_months=dates.duration_months,
        description=block.text,
        date_conflict=dates.date_conflict,
    )


def _education(block: ExtractedBlock) -> EducationItem:
    confidence = _confidence(block, "education")
    return EducationItem(
        item_id=f"education:{block.block_id}",
        origin="extracted",
        extraction_confidence=confidence.value,
        confidence_inputs=confidence.inputs,
        provenance=_provenance(block, "education"),
        source_text=block.text,
        institution=None,
        degree_level=None,
        field_of_study=None,
        start_date=None,
        end_date=None,
        coursework=(),
    )


def _project(block: ExtractedBlock) -> ProjectItem:
    confidence = _confidence(block, "projects")
    return ProjectItem(
        item_id=f"project:{block.block_id}",
        origin="extracted",
        extraction_confidence=confidence.value,
        confidence_inputs=confidence.inputs,
        provenance=_provenance(block, "projects"),
        source_text=block.text,
        name=None,
        description=block.text,
    )


def _certification(block: ExtractedBlock) -> CertificationItem:
    confidence = _confidence(block, "certifications")
    return CertificationItem(
        item_id=f"certification:{block.block_id}",
        origin="extracted",
        extraction_confidence=confidence.value,
        confidence_inputs=confidence.inputs,
        provenance=_provenance(block, "certifications"),
        source_text=block.text,
        name=block.text,
        issuer=None,
        issued=None,
    )


def _achievement(block: ExtractedBlock) -> AchievementItem:
    confidence = _confidence(block, "achievements")
    return AchievementItem(
        item_id=f"achievement:{block.block_id}",
        origin="extracted",
        extraction_confidence=confidence.value,
        confidence_inputs=confidence.inputs,
        provenance=_provenance(block, "achievements"),
        source_text=block.text,
        text=block.text,
    )


def _unclassified(block: ExtractedBlock) -> UnclassifiedItem:
    confidence = _confidence(block, "unclassified")
    return UnclassifiedItem(
        item_id=f"unclassified:{block.block_id}",
        origin="extracted",
        extraction_confidence=confidence.value,
        confidence_inputs=confidence.inputs,
        provenance=_provenance(block, "unclassified"),
        source_text=block.text,
        text=block.text,
    )
