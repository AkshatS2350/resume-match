
from resumematch.core.schemas.readiness import (
    CategoryResult,
    MatchedSignal,
    MissingSignal,
)


def test_readiness_signal_models_preserve_grounding_and_missing_kind() -> None:
    matched = MatchedSignal(signal_id="python", evidence_level=2, supporting_item_ids=("skill-1",))
    missing = MissingSignal(signal_id="sql", kind="below_required_level")
    category = CategoryResult(
        category_id="skills",
        weight=100,
        score=70,
        matched_signals=(matched,),
        missing_signals=(missing,),
        applied_penalties=(),
    )
    assert category.model_validate_json(category.model_dump_json()) == category
