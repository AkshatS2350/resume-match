"""Enforce the approved Public_Job_Data persisted-column allowlist."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from sqlalchemy import MetaData

_ALLOWLIST_PATH = Path(__file__).parents[1] / "docs" / "schemas" / "persisted_columns.txt"


def _allowed_columns(path: Path = _ALLOWLIST_PATH) -> set[tuple[str, str]]:
    return {
        tuple(line.split(",", maxsplit=1))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    }


def _defined_columns(metadata: MetaData) -> set[tuple[str, str]]:
    return {
        (table.name, column.name)
        for table in metadata.tables.values()
        for column in table.columns
    }


def find_unapproved_columns(metadata: MetaData) -> set[tuple[str, str]]:
    """Return persisted columns absent from the checked-in privacy allowlist."""
    return _defined_columns(metadata) - _allowed_columns()


def _format(columns: Iterable[tuple[str, str]]) -> str:
    return ", ".join(f"{table}.{column}" for table, column in sorted(columns))


def main() -> int:
    from resumematch.job.store.schema import metadata

    unapproved = find_unapproved_columns(metadata)
    missing = _allowed_columns() - _defined_columns(metadata)
    if unapproved:
        print(f"unapproved persisted column: {_format(unapproved)}")
    if missing:
        print(f"allowlisted persisted column missing from schema: {_format(missing)}")
    return 1 if unapproved or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
