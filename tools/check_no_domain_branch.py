"""Reject configured rubric identifiers in generic scoring-engine source."""

from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass
from pathlib import Path

IDENTIFIER_PATTERN = re.compile(r"^\s*(?:rubric_id|role_id|domain_id):\s*[\"']?([^\"'\s#]+)")
ENGINE_PATHS = (
    Path("rubric/engine.py"),
    Path("rubric/evidence.py"),
    Path("matching/engine.py"),
    Path("matching/classifier.py"),
)


@dataclass(frozen=True)
class Finding:
    identifier: str
    path: Path
    line: int


def _identifiers(rubric_root: Path) -> frozenset[str]:
    values: set[str] = set()
    for path in sorted(rubric_root.rglob("*.yaml")):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = IDENTIFIER_PATTERN.match(line)
            if match:
                values.add(match.group(1))
    return frozenset(values)


def _package_root(source_root: Path) -> Path:
    return source_root if source_root.name == "resumematch" else source_root / "resumematch"


def find_findings(source_root: Path, rubric_root: Path) -> list[Finding]:
    identifiers = _identifiers(rubric_root)
    package_root = _package_root(source_root)
    findings: list[Finding] = []
    for relative in ENGINE_PATHS:
        path = package_root / relative
        if not path.exists():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value in identifiers
            ):
                findings.append(Finding(node.value, path, node.lineno))
    return sorted(findings, key=lambda finding: (finding.path, finding.line, finding.identifier))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", nargs="?", type=Path, default=Path("backend/src"))
    parser.add_argument("rubric_root", nargs="?", type=Path, default=Path("rubrics"))
    args = parser.parse_args()
    findings = find_findings(args.source_root, args.rubric_root)
    for finding in findings:
        print(f"{finding.path}:{finding.line}: domain_specific_branch: {finding.identifier}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
