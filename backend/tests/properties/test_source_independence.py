from pathlib import Path


def test_matching_has_no_job_adapter_dependency() -> None:
    root = Path(__file__).resolve().parents[3]
    matching = root / "backend" / "src" / "resumematch" / "matching"

    assert "adapters" not in "\n".join(
        path.read_text(encoding="utf-8") for path in matching.glob("*.py")
    )
