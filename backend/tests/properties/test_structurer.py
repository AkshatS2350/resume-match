from datetime import date
from pathlib import Path
from typing import Protocol

from resumematch.core.schemas.extracted_text import ExtractedBlock, ExtractedText
from resumematch.resume.extract.docx import extract_docx
from resumematch.resume.extract.pdf import extract_pdf
from resumematch.resume.structure import structure
from resumematch.resume.structure.sections import load_section_headings
from resumematch.skill.alias_loader import load_aliases
from resumematch.skill.normalizer import SkillNormalizer

ROOT = Path(__file__).resolve().parents[3]


class CountingProvider(Protocol):
    invocations: int


def test_structurer_is_deterministic_and_preserves_block_provenance() -> None:
    extracted = ExtractedText(
        text="Skills\nPython\nExperience\nEngineer Jan 2023 - Present",
        blocks=(
            ExtractedBlock(
                block_id="heading-skills",
                page=1,
                start_offset=0,
                end_offset=6,
                text="Skills",
                section_id="",
                layout_kind="heading",
                column_index=None,
            ),
            ExtractedBlock(
                block_id="skill-python",
                page=1,
                start_offset=7,
                end_offset=13,
                text="Python",
                section_id="",
                layout_kind="list_item",
                column_index=None,
            ),
            ExtractedBlock(
                block_id="heading-experience",
                page=1,
                start_offset=14,
                end_offset=24,
                text="Experience",
                section_id="",
                layout_kind="heading",
                column_index=None,
            ),
            ExtractedBlock(
                block_id="experience-1",
                page=1,
                start_offset=25,
                end_offset=52,
                text="Engineer Jan 2023 - Present",
                section_id="",
                layout_kind="paragraph",
                column_index=None,
            ),
        ),
        page_count=1,
        pages_with_text_layer=(1,),
        extractor_version="test",
    )
    result = structure(
        extracted,
        date(2026, 1, 1),
        load_section_headings(ROOT / "config" / "section_headings.yaml"),
        SkillNormalizer(load_aliases(ROOT / "ontology" / "skills.yaml")),
    )
    assert result == structure(
        extracted,
        date(2026, 1, 1),
        load_section_headings(ROOT / "config" / "section_headings.yaml"),
        SkillNormalizer(load_aliases(ROOT / "ontology" / "skills.yaml")),
    )
    assert result.skills[0].source_text == "Python"
    assert result.skills[0].provenance is not None
    assert result.skills[0].provenance.block_ids == ("skill-python",)
    assert result.experience[0].duration_months == 36


def test_structurer_covers_every_text_bearing_fixture_block_once(
    counting_stub_provider: CountingProvider,
) -> None:
    paths = (
        *(
            ROOT / "fixtures" / "resumes" / f"{index:02d}-{name}.pdf"
            for index, name in (
                (1, "single-column"),
                (2, "two-column"),
                (3, "table-based"),
                (4, "text-box"),
                (5, "multi-page"),
                (6, "missing-sections"),
                (7, "duplicate-headings"),
                (8, "unusual-headings"),
                (9, "malformed-encoding"),
            )
        ),
        ROOT / "fixtures" / "resumes" / "11-docx-resume.docx",
    )
    headings = load_section_headings(ROOT / "config" / "section_headings.yaml")
    normalizer = SkillNormalizer(load_aliases(ROOT / "ontology" / "skills.yaml"))
    for path in paths:
        extracted = extract_docx(path) if path.suffix == ".docx" else extract_pdf(path)
        result = structure(extracted, date(2026, 1, 1), headings, normalizer)
        item_ids = tuple(
            item.provenance.block_ids[0]
            for section in (
                result.skills,
                result.experience,
                result.education,
                result.projects,
                result.certifications,
                result.achievements,
                result.unclassified,
            )
            for item in section
            if item.provenance is not None
        )
        assert sorted(item_ids) == sorted(block.block_id for block in extracted.blocks)
    assert counting_stub_provider.invocations == 0
