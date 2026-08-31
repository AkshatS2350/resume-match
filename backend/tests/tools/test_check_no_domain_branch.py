"""Tests for the no-domain-specific-scoring-branch checker."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CHECKER = REPOSITORY_ROOT / "tools" / "check_no_domain_branch.py"


def test_reports_a_configured_identifier_in_a_synthetic_engine(tmp_path: Path) -> None:
    source_root = tmp_path / "src"
    engine = source_root / "resumematch" / "rubric" / "engine.py"
    engine.parent.mkdir(parents=True)
    engine.write_text('if domain_id == "finance":\n    pass\n', encoding="utf-8")
    rubric_root = tmp_path / "rubrics"
    rubric_root.mkdir()
    (rubric_root / "finance.yaml").write_text(
        "rubric_id: finance.financial_analyst.entry\n"
        "role_id: financial_analyst\n"
        "domain_id: finance\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(CHECKER), str(source_root), str(rubric_root)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "finance" in result.stdout
    assert f"{engine}:1:" in result.stdout


def test_accepts_empty_future_engine_modules_and_rubric_tree(tmp_path: Path) -> None:
    source_root = tmp_path / "src"
    (source_root / "resumematch").mkdir(parents=True)
    rubric_root = tmp_path / "rubrics"
    rubric_root.mkdir()

    result = subprocess.run(
        [sys.executable, str(CHECKER), str(source_root), str(rubric_root)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
