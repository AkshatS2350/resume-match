"""Reject dynamic and shell-based egress escapes outside the two enclaves."""

from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass
from pathlib import Path

EXEMPT_PATHS = (Path("llm/providers"), Path("job/adapters"))
URL_PATTERN = re.compile(r"^(https?|ftp|ws|wss)://")


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str


class EgressVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.findings: list[tuple[int, str]] = []
        self.module_names: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for imported in node.names:
            self.module_names.add(imported.asname or imported.name.split(".")[0])
            if imported.name == "importlib":
                self.findings.append((node.lineno, "importlib_import"))
            if imported.name == "subprocess":
                self.findings.append((node.lineno, "subprocess_import"))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module == "importlib":
            self.findings.append((node.lineno, "importlib_import"))
        if node.module == "subprocess":
            self.findings.append((node.lineno, "subprocess_import"))

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if isinstance(node.func, ast.Name):
            if node.func.id == "__import__":
                self.findings.append((node.lineno, "dynamic_import"))
            elif node.func.id in {"eval", "exec", "compile"}:
                self.findings.append((node.lineno, "dynamic_execution"))
            elif node.func.id == "setattr" and self._sets_module(node):
                self.findings.append((node.lineno, "module_setattr"))
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr == "import_module":
                self.findings.append((node.lineno, "dynamic_import"))
            elif self._is_shell_escape(node.func):
                self.findings.append((node.lineno, "subprocess_execution"))
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:  # noqa: N802
        if isinstance(node.value, str) and URL_PATTERN.match(node.value):
            self.findings.append((node.lineno, "url_literal"))

    def _sets_module(self, node: ast.Call) -> bool:
        return bool(
            node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in self.module_names
        )

    @staticmethod
    def _is_shell_escape(node: ast.Attribute) -> bool:
        return (
            isinstance(node.value, ast.Name)
            and node.value.id == "os"
            and (node.attr in {"system", "popen"} or node.attr.startswith("exec"))
        )


def _package_root(source_root: Path) -> Path:
    return source_root if source_root.name == "resumematch" else source_root / "resumematch"


def find_findings(source_root: Path) -> list[Finding]:
    package_root = _package_root(source_root)
    findings: list[Finding] = []
    for path in sorted(package_root.rglob("*.py")):
        relative = path.relative_to(package_root).parent
        if any(relative == exempt or exempt in relative.parents for exempt in EXEMPT_PATHS):
            continue
        visitor = EgressVisitor()
        visitor.visit(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
        findings.extend(Finding(path, line, rule) for line, rule in visitor.findings)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", nargs="?", type=Path, default=Path("backend/src"))
    args = parser.parse_args()
    findings = find_findings(args.source_root)
    for finding in findings:
        print(f"{finding.path}:{finding.line}: {finding.rule}: prohibited egress escape hatch")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
