"""Fail closed when rubric configuration or its committed schema is invalid."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from resumematch.core.schemas.rubric import RoleRubric  # noqa: E402
from resumematch.rubric.loader import load_rubrics  # noqa: E402
from resumematch.skill.alias_loader import AliasConfigError, load_aliases  # noqa: E402


def validate_config(
    rubric_directory: Path, aliases_path: Path, schema_path: Path
) -> tuple[str, ...]:
    """Return every deterministic validation failure without a bypass path."""

    failures: list[str] = []
    if not schema_path.is_file() or schema_path.read_text(encoding="utf-8") != _schema_text():
        failures.append(f"{schema_path}: schema is stale")
    try:
        aliases = load_aliases(aliases_path)
    except (AliasConfigError, OSError, yaml.YAMLError) as error:
        failures.append(f"{aliases_path}: {error}")
        return tuple(failures)
    result = load_rubrics(rubric_directory, aliases)
    failures.extend(result.failures)
    return tuple(failures)


def _schema_text() -> str:
    return json.dumps(RoleRubric.model_json_schema(), indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rubrics", type=Path, default=ROOT / "rubrics")
    parser.add_argument("--aliases", type=Path, default=ROOT / "ontology" / "skills.yaml")
    parser.add_argument(
        "--schema", type=Path, default=ROOT / "docs" / "schemas" / "role_rubric.schema.json"
    )
    args = parser.parse_args()
    failures = validate_config(args.rubrics, args.aliases, args.schema)
    print("\n".join(failures))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
