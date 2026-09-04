import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_pii_evaluation_reports_recall_and_precision_per_category() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "eval_pii.py")],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "email recall=" in result.stdout
    assert "person_name recall=" in result.stdout
