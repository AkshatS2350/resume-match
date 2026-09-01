from pathlib import Path

from resumematch.resume.extract.docx import extract_docx


def test_docx_extraction_preserves_offsets_and_table_cells() -> None:
    path = Path(__file__).resolve().parents[4] / "fixtures" / "resumes" / "11-docx-resume.docx"
    extracted = extract_docx(path)
    assert any(block.layout_kind == "table_cell" for block in extracted.blocks)
    assert all(
        extracted.text[block.start_offset : block.end_offset] == block.text
        for block in extracted.blocks
    )
