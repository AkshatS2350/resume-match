from pathlib import Path

from resumematch.resume.extract.pdf import extract_pdf


def test_extract_pdf_preserves_block_offsets() -> None:
    path = Path(__file__).resolve().parents[4] / "fixtures" / "resumes" / "02-two-column.pdf"
    extracted = extract_pdf(path)
    assert extracted.page_count == 1
    assert all(
        extracted.text[block.start_offset : block.end_offset] == block.text
        for block in extracted.blocks
    )
    expected = (
        (
            Path(__file__).resolve().parents[4]
            / "fixtures"
            / "baselines"
            / "reading_order"
            / "02-two-column.txt"
        )
        .read_text(encoding="utf-8")
        .strip()
    )
    assert extracted.text == expected
