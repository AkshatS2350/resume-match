"""Configured, deterministic seniority and education extraction."""

import ast
from decimal import Decimal
from pathlib import Path

from resumematch.core.schemas.candidate import DegreeLevel, SeniorityId
from resumematch.job.requirements.education import extract_education
from resumematch.job.requirements.seniority import derive_seniority

_CONFIG = Path(__file__).parents[4] / "config" / "seniority_mapping.yaml"


def test_explicit_title_tokens_map_to_configured_seniority() -> None:
    assert derive_seniority("Summer Intern", None, None, _CONFIG).seniority is SeniorityId.INTERN
    assert derive_seniority("Senior Analyst", None, None, _CONFIG).seniority is SeniorityId.SENIOR
    assert (
        derive_seniority("Head of Engineering", None, None, _CONFIG).seniority
        is SeniorityId.MANAGER
    )


def test_stated_minimum_experience_maps_to_configured_bands() -> None:
    assert derive_seniority("Engineer", Decimal("0"), None, _CONFIG).seniority is SeniorityId.ENTRY
    assert derive_seniority("Engineer", Decimal("3"), None, _CONFIG).seniority is SeniorityId.MID
    assert derive_seniority("Engineer", Decimal("8"), None, _CONFIG).seniority is SeniorityId.LEAD


def test_maximum_only_experience_uses_the_conservative_configured_bands() -> None:
    result = derive_seniority("Engineer", None, Decimal("5"), _CONFIG)

    assert result.seniority is SeniorityId.MID


def test_strong_title_token_wins_while_ambiguous_title_uses_experience() -> None:
    assert (
        derive_seniority("Junior Engineer", Decimal("6"), None, _CONFIG).seniority
        is SeniorityId.ENTRY
    )
    assert derive_seniority("Analyst", Decimal("6"), None, _CONFIG).seniority is SeniorityId.SENIOR


def test_unresolved_seniority_is_unknown_and_derivation_is_versioned_deterministic() -> None:
    first = derive_seniority("Engineer", None, None, _CONFIG)
    second = derive_seniority("Engineer", None, None, _CONFIG)

    assert first == second
    assert first.seniority is SeniorityId.UNKNOWN
    assert first.mapping_version == "seniority_mapping@1"


def test_education_extraction_records_degree_field_and_requirement_kind() -> None:
    required = extract_education("Bachelor's degree in Computer Science required")
    preferred = extract_education("Master's degree in Statistics preferred")

    assert required == ((DegreeLevel.BACHELORS, "Computer Science", "required"),)
    assert preferred == ((DegreeLevel.MASTERS, "Statistics", "preferred"),)


def test_seniority_derivation_has_no_llm_provider_dependency() -> None:
    module = (
        Path(__file__).parents[3] / "src" / "resumematch" / "job" / "requirements" / "seniority.py"
    )
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import | ast.ImportFrom)
        for alias in node.names
    }

    assert all(
        "llm" not in imported.casefold() and "provider" not in imported.casefold()
        for imported in imports
    )
