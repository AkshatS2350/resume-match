"""Tests for the sanitization-record write import boundary."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CHECKER = REPOSITORY_ROOT / "tools" / "check_session_write_boundary.py"


def _write_module(source_root: Path, module_path: str, contents: str) -> Path:
    path = source_root / "resumematch" / module_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")
    return path


def _run_checker(source_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(source_root)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_allows_the_sanitizer_to_import_session_write(tmp_path: Path) -> None:
    source_root = tmp_path / "src"
    _write_module(
        source_root,
        "privacy/sanitizer.py",
        "from resumematch.core.session_write import write_sanitization_record\n",
    )

    result = _run_checker(source_root)

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("module_path", "statement"),
    [
        ("coach/guide.py", "import resumematch.core.session_write\n"),
        ("api/routes.py", "from resumematch.core import session_write\n"),
        ("core/other.py", "from resumematch.core.session_write import write_sanitization_record\n"),
        (
            "privacy/other.py",
            "from resumematch.core.session_write import write_sanitization_record\n",
        ),
    ],
)
def test_rejects_session_write_imports_outside_sanitizer(
    tmp_path: Path, module_path: str, statement: str
) -> None:
    source_root = tmp_path / "src"
    offending_file = _write_module(source_root, module_path, statement)

    result = _run_checker(source_root)

    assert result.returncode != 0
    assert str(offending_file) in result.stdout
    assert "session_write_boundary" in result.stdout
    assert "may not import resumematch.core.session_write" in result.stdout
