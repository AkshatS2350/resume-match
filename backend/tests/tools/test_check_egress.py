"""Tests for the dynamic-egress escape-hatch checker."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CHECKER = REPOSITORY_ROOT / "tools" / "check_egress.py"


def _run(source_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(source_root)],
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    ("source", "rule"),
    [
        ("import importlib\n", "importlib_import"),
        ("importlib.import_module('httpx')\n", "dynamic_import"),
        ("__import__('httpx')\n", "dynamic_import"),
        ("eval('x')\n", "dynamic_execution"),
        ("exec('x = 1')\n", "dynamic_execution"),
        ("compile('x', 'x', 'exec')\n", "dynamic_execution"),
        ("import subprocess\n", "subprocess_import"),
        ("os.system('curl example.com')\n", "subprocess_execution"),
        ("os.popen('curl example.com')\n", "subprocess_execution"),
        ("os.execv('curl', ['curl'])\n", "subprocess_execution"),
        ("endpoint = 'https://example.test/path'\n", "url_literal"),
        ("import target_module\nsetattr(target_module, 'send', object())\n", "module_setattr"),
    ],
)
def test_reports_each_prohibited_egress_escape_hatch_once(
    tmp_path: Path, source: str, rule: str
) -> None:
    source_root = tmp_path / "src"
    path = source_root / "resumematch" / "coach" / "probe.py"
    path.parent.mkdir(parents=True)
    path.write_text(source, encoding="utf-8")

    result = _run(source_root)

    assert result.returncode == 1
    assert result.stdout.count(rule) == 1
    assert f"{path}:" in result.stdout


def test_exempts_an_identical_finding_in_an_egress_enclave(tmp_path: Path) -> None:
    source_root = tmp_path / "src"
    path = source_root / "resumematch" / "llm" / "providers" / "probe.py"
    path.parent.mkdir(parents=True)
    path.write_text("endpoint = 'https://example.test/path'\n", encoding="utf-8")

    result = _run(source_root)

    assert result.returncode == 0, result.stdout + result.stderr
