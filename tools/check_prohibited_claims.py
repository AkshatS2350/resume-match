"""Reject privacy claims prohibited by RM-PRIV-005 in web copy."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def prohibited_claims(config: Path) -> tuple[str, ...]:
    data = yaml.safe_load(config.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        raise ValueError(f"{config}: claims")
    return tuple(str(claim).lower() for claim in data["claims"])


def find_claims(copy_root: Path, claims: tuple[str, ...]) -> list[str]:
    findings: list[str] = []
    for path in sorted(copy_root.rglob("*")):
        if not path.is_file() or path.suffix not in {".ts", ".tsx"}:
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            lowered = line.lower()
            for claim in claims:
                if claim in lowered:
                    findings.append(f"{path}:{line_number}: prohibited_claim: {claim}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("copy_root", nargs="?", type=Path, default=Path("web/src"))
    parser.add_argument("--config", type=Path, default=Path("config/prohibited_claims.yaml"))
    args = parser.parse_args()
    findings = find_claims(args.copy_root, prohibited_claims(args.config))
    print("\n".join(findings))
    return int(bool(findings))


if __name__ == "__main__":
    raise SystemExit(main())
