"""Deterministic heading-gazetteer section assignment."""

from dataclasses import dataclass
from pathlib import Path

import yaml

from resumematch.core.schemas.extracted_text import ExtractedBlock
from resumematch.skill.fold import fold

_SECTION_IDS = (
    "summary",
    "skills",
    "experience",
    "education",
    "projects",
    "certifications",
    "achievements",
)


class SectionHeadingConfigError(ValueError):
    """Raised when the versioned heading gazetteer is invalid."""


@dataclass(frozen=True)
class SectionHeadings:
    version: str
    by_folded_heading: dict[str, str]


def load_section_headings(path: Path) -> SectionHeadings:
    """Load a complete, unambiguous ``section_headings@1`` gazetteer."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != "section_headings@1":
        raise SectionHeadingConfigError(f"{path}: version")
    sections = data.get("sections")
    if not isinstance(sections, dict) or set(sections) != set(_SECTION_IDS):
        raise SectionHeadingConfigError(f"{path}: sections")
    by_heading: dict[str, str] = {}
    for section_id in _SECTION_IDS:
        aliases = sections[section_id]
        if (
            not isinstance(aliases, list)
            or not aliases
            or not all(isinstance(alias, str) for alias in aliases)
        ):
            raise SectionHeadingConfigError(f"{path}: {section_id}")
        for alias in aliases:
            folded = fold(alias)
            existing = by_heading.get(folded)
            if existing is not None and existing != section_id:
                raise SectionHeadingConfigError(f"{path}: duplicate heading {folded!r}")
            by_heading[folded] = section_id
    return SectionHeadings("section_headings@1", by_heading)


def assign_sections(
    blocks: tuple[ExtractedBlock, ...], headings: SectionHeadings
) -> dict[str, tuple[str, ...]]:
    """Assign every block exactly once; ambiguous heading regions fail safely closed."""
    assigned: dict[str, list[str]] = {section_id: [] for section_id in _SECTION_IDS}
    assigned["unclassified"] = []
    seen_sections: set[str] = set()
    active_section = "unclassified"
    for block in blocks:
        if block.layout_kind == "heading":
            section_id = headings.by_folded_heading.get(fold(block.text))
            if section_id is None or section_id in seen_sections:
                active_section = "unclassified"
            else:
                seen_sections.add(section_id)
                active_section = section_id
        assigned[active_section].append(block.block_id)
    section_ids = (*_SECTION_IDS, "unclassified")
    return {section_id: tuple(assigned[section_id]) for section_id in section_ids}
