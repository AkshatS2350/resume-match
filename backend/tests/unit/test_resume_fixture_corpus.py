from pathlib import Path

CORPUS = Path(__file__).resolve().parents[3] / "fixtures" / "resumes"


def test_resume_fixture_corpus_has_required_formats_and_one_image_only_pdf() -> None:
    documents = sorted(path for path in CORPUS.iterdir() if path.suffix in {".pdf", ".docx"})

    assert len(documents) == 11
    assert sum(path.name == "10-image-only.pdf" for path in documents) == 1
    assert any(path.suffix == ".docx" for path in documents)
