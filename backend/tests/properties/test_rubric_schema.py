import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from resumematch.core.schemas.rubric import RoleRubric


def _payload() -> dict[str, object]:
    return {
        "schema_version": "role_rubric/1", "rubric_id": "r", "role_id": "role",
        "role_family": "finance", "domain_id": "finance", "seniority_id": "entry",
        "rubric_version": "1", "status": "draft", "weight_basis": "expert",
        "weight_basis_note": "note", "experience_bands": [],
        "education_expectations": {
            "min_degree_level": "bachelors", "preferred_fields": [], "required": False,
        },
        "certification_expectations": [], "categories": [], "penalties": [],
    }


@given(st.sampled_from(("draft", "reviewed", "stable")))
def test_rubric_schema_round_trips(status: str) -> None:
    rubric = RoleRubric.model_validate({**_payload(), "status": status})
    assert RoleRubric.model_validate_json(rubric.model_dump_json()) == rubric


def test_rubric_schema_closes_status_and_signal_condition_vocabularies() -> None:
    payload = _payload()
    with pytest.raises(ValidationError):
        RoleRubric.model_validate({**payload, "status": "other"})
    with pytest.raises(ValidationError):
        RoleRubric.model_validate({**payload, "penalties": [{
            "penalty_id": "p", "applies_to_category": "category", "points": "1",
            "condition": {"kind": "arbitrary_code"},
        }]})
