"""Closed operation specifications for value-free LLM projection admission."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from resumematch.llm.projection import FieldPath, LLMOperation


class GroundedStatement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    cited_evidence_ids: list[str] = Field(min_length=1)
    cited_skill_ids: list[str] = Field(default_factory=list)


class UnknownValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    unknown: Literal[True]


class ReadinessExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statements: list[GroundedStatement]
    unresolved: list[str] = Field(default_factory=list)


class DimensionNote(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension_id: str
    note: GroundedStatement | UnknownValue


class MatchExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statements: list[GroundedStatement]
    dimension_notes: list[DimensionNote]


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["reorder", "emphasize", "quantify", "reword"]
    text: str
    cited_item_ids: list[str] = Field(min_length=1)
    cited_requirement_offsets: list[tuple[int, int]] = Field(default_factory=list)


class ApplicationGuidanceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendations: list[Recommendation]
    deprioritize: list[GroundedStatement] = Field(default_factory=list)


class GapNote(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical_skill_id: str
    learning_note: str


class SkillGapSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gaps: list[GapNote]


class ExtractedField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_path: str
    value: str | UnknownValue
    source_offsets: tuple[int, int] | None


class BoundedExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fields: list[ExtractedField]


class LLMOperationSpec(BaseModel):
    """A single authoritative declaration of an operation's required paths."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    operation: LLMOperation
    response_model: type[BaseModel]
    required_candidate_paths: tuple[FieldPath, ...]
    budget_config_version: str


OPERATION_SPECS: dict[LLMOperation, LLMOperationSpec] = {
    "explain_readiness": LLMOperationSpec(
        operation="explain_readiness",
        response_model=ReadinessExplanation,
        required_candidate_paths=(
            FieldPath("/target/role_id"),
            FieldPath("/target/domain_id"),
            FieldPath("/skills/*/canonical_id"),
            FieldPath("/skills/*/evidence_level"),
        ),
        budget_config_version="budget_priority@1",
    ),
    "explain_match": LLMOperationSpec(
        operation="explain_match",
        response_model=MatchExplanation,
        required_candidate_paths=(
            FieldPath("/target/role_id"),
            FieldPath("/skills/*/canonical_id"),
            FieldPath("/skills/*/evidence_level"),
            FieldPath("/experience/*/item_id"),
        ),
        budget_config_version="budget_priority@1",
    ),
    "generate_application_guidance": LLMOperationSpec(
        operation="generate_application_guidance",
        response_model=ApplicationGuidanceResponse,
        required_candidate_paths=(
            FieldPath("/skills/*/canonical_id"),
            FieldPath("/skills/*/evidence_level"),
            FieldPath("/experience/*/item_id"),
            FieldPath("/experience/*/title"),
        ),
        budget_config_version="budget_priority@1",
    ),
    "summarize_skill_gaps": LLMOperationSpec(
        operation="summarize_skill_gaps",
        response_model=SkillGapSummary,
        required_candidate_paths=(
            FieldPath("/skills/*/canonical_id"),
            FieldPath("/skills/*/evidence_level"),
        ),
        budget_config_version="budget_priority@1",
    ),
    "bounded_extract": LLMOperationSpec(
        operation="bounded_extract",
        response_model=BoundedExtraction,
        required_candidate_paths=(FieldPath("/unclassified/*/text"),),
        budget_config_version="budget_priority@1",
    ),
}


def operation_spec(operation: LLMOperation) -> LLMOperationSpec:
    """Return the sole specification for one of the five approved operations."""

    return OPERATION_SPECS[operation]
