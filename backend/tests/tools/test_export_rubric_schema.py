"""Role-rubric schema export and configuration-validation gate tests."""

from __future__ import annotations

import runpy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
EXPORTER = ROOT / "tools" / "export_schemas.py"
VALIDATOR = ROOT / "tools" / "validate_rubric_config.py"


def test_role_rubric_schema_export_is_deterministic() -> None:
    exporter = runpy.run_path(str(EXPORTER))
    main = exporter["main"]
    main()
    schema_path = ROOT / "docs" / "schemas" / "role_rubric.schema.json"
    first = schema_path.read_bytes()

    main()

    assert schema_path.read_bytes() == first


def test_openapi_type_export_converts_component_names_to_typescript_identifiers() -> None:
    exporter = runpy.run_path(str(EXPORTER))
    exporter["main"]()
    declarations = (ROOT / "web" / "src" / "lib" / "api" / "generated" / "openapi.ts").read_text(
        encoding="utf-8"
    )

    assert "export interface AchievementItem_Input" in declarations
    assert "export interface AchievementItem-Input" not in declarations


@pytest.mark.parametrize(
    "replacement, changed, expected",
    (
        ("weight: 100", "weight: 99", "weights"),
            ("status: draft", "status: unpublished", "status"),
            ("rubric_id: test.role", "unexpected: value\nrubric_id: test.role", "unexpected"),
            ("weight_basis_note: test", "", "weight_basis_note"),
            (
                "experience_bands: []",
                "experience_bands:\n"
                "  - band_id: entry\n"
                "    min_years: 0\n"
                "    max_years: 1\n"
                "    score: invalid",
                "score",
            ),
    ),
)
def test_config_validation_fails_closed_for_invalid_rubric_fields(
    replacement: str, changed: str, expected: str, tmp_path: Path
) -> None:
    checker = runpy.run_path(str(VALIDATOR))
    rubric = tmp_path / "invalid.yaml"
    rubric.write_text(_rubric().replace(replacement, changed), encoding="utf-8")

    failures = checker["validate_config"](
        tmp_path,
        ROOT / "ontology" / "skills.yaml",
        ROOT / "docs" / "schemas" / "role_rubric.schema.json",
    )

    assert len(failures) == 1
    assert expected in failures[0]


def test_config_validation_rejects_a_stale_schema(tmp_path: Path) -> None:
    checker = runpy.run_path(str(VALIDATOR))
    stale = tmp_path / "role_rubric.schema.json"
    stale.write_text("{}\n", encoding="utf-8")

    failures = checker["validate_config"](
        tmp_path,
        ROOT / "ontology" / "skills.yaml",
        stale,
    )

    assert failures == (f"{stale}: schema is stale",)


def test_local_validation_command_exits_nonzero_for_invalid_rubric(tmp_path: Path) -> None:
    rubric = tmp_path / "invalid.yaml"
    rubric.write_text(_rubric().replace("weight: 100", "weight: 99"), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--rubrics",
            str(tmp_path),
            "--aliases",
            str(ROOT / "ontology" / "skills.yaml"),
            "--schema",
            str(ROOT / "docs" / "schemas" / "role_rubric.schema.json"),
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 1
    assert "weights" in result.stdout


def _rubric() -> str:
    return """schema_version: role_rubric/1
rubric_id: test.role
role_id: role
role_family: finance
domain_id: finance
seniority_id: entry
rubric_version: "1"
status: draft
weight_basis: expert_judgement
weight_basis_note: test
experience_bands: []
education_expectations: {min_degree_level: bachelors, preferred_fields: [], required: false}
certification_expectations: []
categories:
  - category_id: core
    weight: 100
    signals:
      - signal_id: known
        type: skill
        target: {target_type: canonical_skill, target_id: python}
        weight: 1
        min_evidence_level: 1
        required: false
penalties: []
"""
