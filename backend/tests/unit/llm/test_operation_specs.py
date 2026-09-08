"""The five LLM operations have one closed, schema-owned path declaration."""

from resumematch.llm.schemas.operations import OPERATION_SPECS, operation_spec


def test_operation_specs_match_the_design_required_path_table() -> None:
    assert set(OPERATION_SPECS) == {
        "explain_readiness",
        "explain_match",
        "generate_application_guidance",
        "summarize_skill_gaps",
        "bounded_extract",
    }
    assert tuple(map(str, operation_spec("explain_readiness").required_candidate_paths)) == (
        "/target/role_id",
        "/target/domain_id",
        "/skills/*/canonical_id",
        "/skills/*/evidence_level",
    )
    assert tuple(map(str, operation_spec("explain_match").required_candidate_paths)) == (
        "/target/role_id",
        "/skills/*/canonical_id",
        "/skills/*/evidence_level",
        "/experience/*/item_id",
    )
    guidance_paths = operation_spec("generate_application_guidance").required_candidate_paths
    assert tuple(map(str, guidance_paths)) == (
        "/skills/*/canonical_id",
        "/skills/*/evidence_level",
        "/experience/*/item_id",
        "/experience/*/title",
    )
    assert tuple(map(str, operation_spec("summarize_skill_gaps").required_candidate_paths)) == (
        "/skills/*/canonical_id",
        "/skills/*/evidence_level",
    )
    assert tuple(map(str, operation_spec("bounded_extract").required_candidate_paths)) == (
        "/unclassified/*/text",
    )


def test_operation_specs_bind_response_models_and_expose_no_second_ineligibility_list() -> None:
    for operation, specification in OPERATION_SPECS.items():
        assert specification.operation == operation
        assert specification.response_model.model_config["extra"] == "forbid"
        assert not hasattr(specification, "ineligible_paths")
        assert specification.budget_config_version == "budget_priority@1"
