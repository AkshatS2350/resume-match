"""Enforce the sanitization-record write import boundary."""

from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

ALLOWED_MODULE = "resumematch.privacy.sanitizer"
SESSION_WRITE_MODULE = "resumematch.core.session_write"
RULE_NAME = "session_write_boundary"


@dataclass(frozen=True)
class Violation:
    """A prohibited reference to the session-write capability."""

    path: Path
    line: int
    detail: str


class SessionWriteReferenceVisitor(ast.NodeVisitor):
    """Find imports and literal dynamic imports of the private capability."""

    def __init__(self) -> None:
        self.details: list[tuple[int, str]] = []

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for imported in node.names:
            if imported.name == SESSION_WRITE_MODULE:
                self.details.append((node.lineno, "direct import"))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module == SESSION_WRITE_MODULE:
            self.details.append((node.lineno, "from-module import"))
        elif node.module == "resumematch.core" and any(
            imported.name == "session_write" for imported in node.names
        ):
            self.details.append((node.lineno, "core package import"))

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if self._is_dynamic_import(node) and self._loads_session_write(node):
            self.details.append((node.lineno, "dynamic import"))
        self.generic_visit(node)

    @staticmethod
    def _is_dynamic_import(node: ast.Call) -> bool:
        if isinstance(node.func, ast.Name):
            return node.func.id == "__import__"
        return (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "import_module"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "importlib"
        )

    @staticmethod
    def _loads_session_write(node: ast.Call) -> bool:
        return bool(
            node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == SESSION_WRITE_MODULE
        )


def _package_root(source_root: Path) -> Path:
    return source_root if source_root.name == "resumematch" else source_root / "resumematch"


def _module_name(package_root: Path, path: Path) -> str:
    relative = path.relative_to(package_root).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(("resumematch", *parts))


def find_violations(source_root: Path) -> Iterable[Violation]:
    """Yield prohibited session-write capability references in sorted path order."""

    package_root = _package_root(source_root)
    for path in sorted(package_root.rglob("*.py")):
        if _module_name(package_root, path) == ALLOWED_MODULE:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        visitor = SessionWriteReferenceVisitor()
        visitor.visit(tree)
        for line, detail in visitor.details:
            yield Violation(path=path, line=line, detail=detail)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source_root",
        nargs="?",
        type=Path,
        default=Path("backend/src"),
        help="directory containing the resumematch package (default: backend/src)",
    )
    args = parser.parse_args()
    violations = list(find_violations(args.source_root))
    for violation in violations:
        print(
            f"{violation.path}:{violation.line}: {RULE_NAME}: "
            f"{violation.detail}; this module may not import "
            f"{SESSION_WRITE_MODULE}"
        )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
