"""Reject non-deterministic constructs in scoring and fixture-loading paths."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

SCORING_PATHS = (Path("rubric"), Path("matching"), Path("job/requirements"))
FIXTURE_PATH = Path("job/adapters/fixture.py")
MAPPING_METHODS = {"keys", "values", "items"}
FIXTURE_ORDER_METHODS = {"listdir", "iterdir", "glob", "scandir"}


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str


class DeterminismVisitor(ast.NodeVisitor):
    def __init__(self, fixture_path: bool) -> None:
        self.fixture_path = fixture_path
        self.findings: list[tuple[int, str]] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if isinstance(node.func, ast.Name):
            if node.func.id == "float":
                self.findings.append((node.lineno, "float_conversion"))
            elif node.func.id == "round":
                self.findings.append((node.lineno, "builtin_round"))
        elif isinstance(node.func, ast.Attribute):
            if self._is_wall_clock_call(node.func):
                self.findings.append((node.lineno, "wall_clock"))
            elif self.fixture_path and node.func.attr in FIXTURE_ORDER_METHODS:
                self.findings.append((node.lineno, "fixture_filesystem_order"))
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:  # noqa: N802
        self._check_iteration(node.iter, node.lineno)
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:  # noqa: N802
        self._check_comprehensions(node.generators)
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:  # noqa: N802
        self._check_comprehensions(node.generators)
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:  # noqa: N802
        self._check_comprehensions(node.generators)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:  # noqa: N802
        self._check_comprehensions(node.generators)
        self.generic_visit(node)

    def _check_comprehensions(self, generators: list[ast.comprehension]) -> None:
        for generator in generators:
            self._check_iteration(generator.iter, generator.iter.lineno)

    def _check_iteration(self, iterable: ast.expr, line: int) -> None:
        if self._is_mapping_view(iterable):
            self.findings.append((line, "unordered_mapping_iteration"))

    @staticmethod
    def _is_mapping_view(node: ast.expr) -> bool:
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in MAPPING_METHODS
        )

    @staticmethod
    def _is_wall_clock_call(node: ast.Attribute) -> bool:
        if not isinstance(node.value, ast.Name):
            return False
        return (
            node.value.id == "datetime" and node.attr in {"now", "utcnow", "today"}
        ) or (node.value.id == "date" and node.attr == "today") or (
            node.value.id == "time" and node.attr in {"time", "monotonic"}
        )


def _package_root(source_root: Path) -> Path:
    return source_root if source_root.name == "resumematch" else source_root / "resumematch"


def _is_scoring_path(relative: Path) -> bool:
    return any(relative == scoped or scoped in relative.parents for scoped in SCORING_PATHS)


def find_findings(source_root: Path) -> list[Finding]:
    package_root = _package_root(source_root)
    findings: list[Finding] = []
    for path in sorted(package_root.rglob("*.py")):
        relative = path.relative_to(package_root)
        scoped = _is_scoring_path(relative.parent)
        fixture = relative == FIXTURE_PATH
        if not scoped and not fixture:
            continue
        visitor = DeterminismVisitor(fixture)
        visitor.visit(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
        findings.extend(Finding(path, line, rule) for line, rule in visitor.findings)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", nargs="?", type=Path, default=Path("backend/src"))
    args = parser.parse_args()
    findings = find_findings(args.source_root)
    for finding in findings:
        print(f"{finding.path}:{finding.line}: {finding.rule}: deterministic path violation")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
