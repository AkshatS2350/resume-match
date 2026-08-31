"""Tests for the deterministic-scoring static checker."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CHECKER = REPOSITORY_ROOT / "tools" / "check_determinism.py"


def _run(source_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(source_root)],
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    ("module_path", "source", "rule"),
    [
        ("rubric/probe.py", "datetime.now()\n", "wall_clock"),
        ("matching/probe.py", "date.today()\n", "wall_clock"),
        ("job/requirements/probe.py", "time.monotonic()\n", "wall_clock"),
        ("rubric/probe.py", "value = float('1.0')\n", "float_conversion"),
        ("matching/probe.py", "value = round(1)\n", "builtin_round"),
        (
            "job/requirements/probe.py",
            "for key in values.keys():\n    pass\n",
            "unordered_mapping_iteration",
        ),
        (
            "job/adapters/fixture.py",
            "for path in root.iterdir():\n    pass\n",
            "fixture_filesystem_order",
        ),
    ],
)
def test_reports_each_determinism_violation_once(
    tmp_path: Path, module_path: str, source: str, rule: str
) -> None:
    source_root = tmp_path / "src"
    path = source_root / "resumematch" / module_path
    path.parent.mkdir(parents=True)
    path.write_text(source, encoding="utf-8")

    result = _run(source_root)

    assert result.returncode == 1
    assert result.stdout.count(rule) == 1
    assert f"{path}:" in result.stdout


def test_accepts_sorted_mapping_iteration(tmp_path: Path) -> None:
    source_root = tmp_path / "src"
    path = source_root / "resumematch" / "rubric" / "probe.py"
    path.parent.mkdir(parents=True)
    path.write_text("for key in sorted(values.keys()):\n    pass\n", encoding="utf-8")

    result = _run(source_root)

    assert result.returncode == 0, result.stdout + result.stderr
