from pathlib import Path

from resumematch.core.schemas.extracted_text import ExtractedBlock
from resumematch.resume.extract.docx import extract_docx
from resumematch.resume.extract.pdf import extract_pdf
from resumematch.resume.structure.sections import assign_sections, load_section_headings

_ROOT = Path(__file__).parents[4]


def _block(block_id: str, text: str, layout_kind: str = "paragraph") -> ExtractedBlock:
    return ExtractedBlock(
        block_id=block_id,
        section_id="preamble",
        page=1,
        start_offset=len(block_id),
        end_offset=len(block_id) + len(text),
        text=text,
        layout_kind=layout_kind,  # type: ignore[arg-type]
        column_index=None,
    )


def test_assignment_routes_known_heading_content_without_dropping_blocks() -> None:
    headings = load_section_headings(_ROOT / "config" / "section_headings.yaml")
    blocks = (
        _block("1", "Avery Rowan"),
        _block("2", "Experience", "heading"),
        _block("3", "Built deterministic reports."),
        _block("4", "Skills", "heading"),
        _block("5", "Python"),
    )

    assigned = assign_sections(blocks, headings)

    assert assigned["experience"] == ("2", "3")
    assert assigned["skills"] == ("4", "5")
    assert assigned["unclassified"] == ("1",)
    assert sorted(block_id for section in assigned.values() for block_id in section) == [
        "1",
        "2",
        "3",
        "4",
        "5",
    ]


def test_duplicate_and_unrecognized_headings_route_content_to_unclassified() -> None:
    headings = load_section_headings(_ROOT / "config" / "section_headings.yaml")
    blocks = (
        _block("1", "Experience", "heading"),
        _block("2", "First role"),
        _block("3", "Experience", "heading"),
        _block("4", "Second role"),
        _block("5", "Things I Have Built", "heading"),
        _block("6", "Project detail"),
    )

    assigned = assign_sections(blocks, headings)

    assert assigned["experience"] == ("1", "2")
    assert assigned["unclassified"] == ("3", "4", "5", "6")


def test_all_text_bearing_fixtures_assign_every_block_once() -> None:
    headings = load_section_headings(_ROOT / "config" / "section_headings.yaml")
    fixtures = _ROOT / "fixtures" / "resumes"
    extracted = [
        *(extract_pdf(path) for path in sorted(fixtures.glob("0[1-9]-*.pdf"))),
        extract_docx(fixtures / "11-docx-resume.docx"),
    ]

    for document in extracted:
        assigned = assign_sections(document.blocks, headings)
        block_ids = [block_id for section in assigned.values() for block_id in section]
        assert sorted(block_ids) == sorted(block.block_id for block in document.blocks)
