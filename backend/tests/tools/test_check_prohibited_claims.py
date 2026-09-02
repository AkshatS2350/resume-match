from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / "tools" / "check_prohibited_claims.py"


def _run(copy_root: Path, config: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(copy_root), "--config", str(config)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_each_prohibited_claim_is_reported_once(tmp_path: Path) -> None:
    claims = ("never leaves your device", "anonymous", "no data touches disk")
    copy = tmp_path / "copy.tsx"
    copy.write_text("\n".join(claims), encoding="utf-8")
    config = ROOT / "config" / "prohibited_claims.yaml"
    result = _run(tmp_path, config)
    assert result.returncode == 1
    assert result.stdout.count("copy.tsx:") == len(claims)


def test_current_copy_has_no_prohibited_claim() -> None:
    result = _run(ROOT / "web" / "src", ROOT / "config" / "prohibited_claims.yaml")
    assert result.returncode == 0
