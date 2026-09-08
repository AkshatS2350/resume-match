from decimal import Decimal

from resumematch.core.schemas.candidate import (
    ExperienceItem,
    SkillItem,
    StructuredResume,
    TargetConstraints,
    UnclassifiedItem,
)
from resumematch.core.schemas.sanitized import SanitizedResume
from resumematch.llm.projection import (
    ProjectionRequest,
    expand_operation_paths,
    resolve,
    resolve_operation,
    resolves,
)


def _sanitized() -> SanitizedResume:
    return SanitizedResume(
        schema_version="sanitized_resume/1",
        source_profile_revision=1,
        resume=StructuredResume(
            schema_version="structured_resume/1",
            summary=None,
            skills=(
                SkillItem(
                    item_id="skill-1",
                    origin="user_provided",
                    extraction_confidence=Decimal("1.00"),
                    confidence_inputs=(),
                    provenance=None,
                    source_text="redacted value",
                    surface="Python",
                    canonical_skill_id="python",
                ),
            ),
            experience=(),
            education=(),
            projects=(),
            certifications=(),
            achievements=(),
            unclassified=(),
        ),
        target=TargetConstraints(
            domain_id="domain", role_id="role", seniority_id="entry", locations=(), work_modes=()
        ),
        removed_span_counts={},
    )


def test_request_is_value_free_and_pointers_resolve_without_raising() -> None:
    request = ProjectionRequest(
        operation="explain_readiness",
        sanitization_content_hash="sha256:" + "0" * 64,
        paths=("/target/role_id",),
        evidence_item_ids=("item-1",),
        permitted_skill_ids=("python",),
        non_candidate_context=None,
    )
    assert request.paths == ("/target/role_id",)
    assert resolves(_sanitized(), "/target/role_id")
    assert resolve(_sanitized(), "/target/role_id") == "role"
    assert resolves(_sanitized(), "/resume/skills/0/canonical_skill_id")
    assert resolves(_sanitized(), "/missing") is False


def test_projection_request_has_only_the_approved_value_free_fields() -> None:
    assert tuple(ProjectionRequest.model_fields) == (
        "operation",
        "sanitization_content_hash",
        "paths",
        "evidence_item_ids",
        "permitted_skill_ids",
        "non_candidate_context",
    )


def test_operation_paths_are_rooted_at_the_inner_sanitized_resume() -> None:
    sanitized = _sanitized()

    assert resolve_operation(sanitized, "/skills/0/canonical_skill_id") == "python"
    assert resolves(sanitized, "/resume/skills/0/canonical_skill_id")


def test_operation_wildcards_expand_in_sorted_resume_root_order() -> None:
    assert expand_operation_paths(_sanitized(), "/skills/*/canonical_skill_id") == (
        "/skills/0/canonical_skill_id",
    )


def test_operation_paths_for_skills_experience_and_unclassified_use_the_resume_root() -> None:
    sanitized = _sanitized()
    resume = sanitized.resume.model_copy(
        update={
            "experience": (
                ExperienceItem(
                    item_id="experience-1",
                    origin="user_provided",
                    extraction_confidence=Decimal("1.00"),
                    confidence_inputs=(),
                    provenance=None,
                    source_text="redacted experience",
                    employer=None,
                    title="Engineer",
                    start_date=None,
                    end_date=None,
                    is_present=False,
                    duration_months=None,
                    description=None,
                    date_conflict=False,
                ),
            ),
            "unclassified": (
                UnclassifiedItem(
                    item_id="unclassified-1",
                    origin="user_provided",
                    extraction_confidence=Decimal("1.00"),
                    confidence_inputs=(),
                    provenance=None,
                    source_text="redacted unclassified",
                    text="unclassified",
                ),
            ),
        }
    )
    with_items = sanitized.model_copy(update={"resume": resume})

    assert expand_operation_paths(with_items, "/skills/*/canonical_skill_id") == (
        "/skills/0/canonical_skill_id",
    )
    assert expand_operation_paths(with_items, "/experience/*/title") == ("/experience/0/title",)
    assert expand_operation_paths(with_items, "/unclassified/*/text") == (
        "/unclassified/0/text",
    )
