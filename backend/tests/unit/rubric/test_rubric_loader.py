from pathlib import Path

import pytest

from resumematch.rubric.loader import RubricLoadError, load_rubrics
from resumematch.skill.alias_loader import load_aliases

ROOT = Path(__file__).resolve().parents[4]


def _rubric(skill: str, *, role: str = "role", weight: int = 100) -> str:
    return f'''schema_version: role_rubric/1
rubric_id: test.{role}
role_id: {role}
role_family: finance
domain_id: finance
seniority_id: entry
rubric_version: "1"
status: draft
weight_basis: expert_judgement
weight_basis_note: test
experience_bands: []
education_expectations: {{min_degree_level: bachelors, preferred_fields: [], required: false}}
certification_expectations: []
categories:
  - category_id: core
    weight: {weight}
    signals:
      - {{signal_id: known, type: skill, canonical_skill_id: {skill}, weight: 1,
         min_evidence_level: 1, required: false}}
penalties: []
'''


def test_loader_rejects_bad_weight_and_unknown_skill_with_path(tmp_path: Path) -> None:
    aliases = load_aliases(ROOT / "ontology" / "skills.yaml")
    bad = tmp_path / "bad.yaml"
    bad.write_text(_rubric("not-in-aliases", weight=99), encoding="utf-8")
    result = load_rubrics(tmp_path, aliases)
    assert result.loaded == ()
    assert str(bad) in result.failures[0]
    assert "weights" in result.failures[0]


def test_loader_rejects_duplicate_identity_and_keeps_valid_rubrics(tmp_path: Path) -> None:
    aliases = load_aliases(ROOT / "ontology" / "skills.yaml")
    first = tmp_path / "first.yaml"
    second = tmp_path / "second.yaml"
    first.write_text(_rubric("python"), encoding="utf-8")
    second.write_text(_rubric("python"), encoding="utf-8")
    result = load_rubrics(tmp_path, aliases)
    assert len(result.loaded) == 1
    assert str(first) in result.failures[0] and str(second) in result.failures[0]
    with pytest.raises(RubricLoadError):
        result.require("unknown", "finance", "entry")
