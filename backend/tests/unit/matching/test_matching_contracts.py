"""Generic, versioned matching contract primitives."""

from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from resumematch.matching.config import load_match_config
from resumematch.matching.contracts import (
    DimensionId,
    DimensionScore,
    EnablementReason,
    EnablementVerdict,
    EvidenceIndex,
    EvidenceLevel,
    EvidenceRef,
    MatchConfig,
    load_matching_contract,
)

_CONFIG = Path(__file__).parents[4] / "config" / "matching_contract.yaml"


def test_contract_config_defines_exactly_the_generic_v1_dimension_ids() -> None:
    contract = load_matching_contract(_CONFIG)

    assert contract.version == "matching_contract@1"
    assert contract.dimension_ids == frozenset(DimensionId)


def test_enablement_verdict_is_frozen_and_forbids_extra_fields() -> None:
    verdict = EnablementVerdict(
        dimension_id=DimensionId.SKILLS,
        enabled=True,
        reason=EnablementReason.ENABLED_BY_CONFIG,
    )

    with pytest.raises(ValidationError):
        verdict.enabled = False  # type: ignore[misc]
    with pytest.raises(ValidationError):
        EnablementVerdict.model_validate({**verdict.model_dump(), "unexpected": True})


def test_dimension_score_requires_decimal_normalized_values_and_exact_weighting() -> None:
    score = DimensionScore(
        dimension_id=DimensionId.SKILLS,
        enabled=True,
        score=Decimal("0.70"),
        weight=Decimal("0.30"),
        weighted_score=Decimal("0.2100"),
        evidence_level=EvidenceLevel.LEVEL_3,
        reason="enabled_by_config",
    )

    assert score.weighted_score == Decimal("0.2100")
    with pytest.raises(ValidationError):
        DimensionScore(
            dimension_id=DimensionId.SKILLS,
            enabled=True,
            score=0.7,
            weight=Decimal("0.30"),
            weighted_score=Decimal("0.21"),
            evidence_level=None,
            reason="enabled_by_config",
        )
    with pytest.raises(ValidationError):
        DimensionScore(
            dimension_id=DimensionId.SKILLS,
            enabled=True,
            score=Decimal("85"),
            weight=Decimal("0.30"),
            weighted_score=Decimal("25.50"),
            evidence_level=None,
            reason="enabled_by_config",
        )
    with pytest.raises(ValidationError):
        DimensionScore(
            dimension_id=DimensionId.SKILLS,
            enabled=True,
            score=Decimal("1.01"),
            weight=Decimal("0.30"),
            weighted_score=Decimal("0.303"),
            evidence_level=None,
            reason="enabled_by_config",
        )


def test_disabled_dimension_requires_null_scores() -> None:
    with pytest.raises(ValidationError):
        DimensionScore(
            dimension_id=DimensionId.SKILLS,
            enabled=False,
            score=Decimal("0.20"),
            weight=Decimal("0.30"),
            weighted_score=Decimal("0.06"),
            evidence_level=None,
            reason="insufficient_job_data",
        )


def test_evidence_index_is_frozen_structured_and_sorted_without_candidate_text() -> None:
    first = EvidenceRef(
        item_id="item-b",
        item_type="experience",
        evidence_level=EvidenceLevel.LEVEL_2,
        dimension_id=DimensionId.SKILLS,
    )
    second = EvidenceRef(
        item_id="item-a",
        item_type="skill",
        evidence_level=EvidenceLevel.LEVEL_3,
        dimension_id=DimensionId.SKILLS,
    )
    index = EvidenceIndex(
        by_dimension={DimensionId.SKILLS: (first, second)},
        evidence_index_version="evidence_index@1",
    )

    assert [reference.item_id for reference in index.by_dimension[DimensionId.SKILLS]] == [
        "item-a",
        "item-b",
    ]
    with pytest.raises(ValidationError):
        EvidenceIndex.model_validate(
            {"evidence_index_version": "evidence_index@1", "resume_text": "raw"}
        )


def test_match_config_is_frozen_decimal_only_and_rejects_unknown_dimensions() -> None:
    config = MatchConfig(
        matching_contract_version="matching_contract@1",
        enablement_rules_version="enablement_rules@1",
        dimension_weights={dimension: Decimal("0.10") for dimension in DimensionId},
        enabled_dimensions=tuple(DimensionId),
    )

    assert config.dimension_weights[DimensionId.SKILLS] == Decimal("0.10")
    with pytest.raises(ValidationError):
        MatchConfig(
            matching_contract_version="matching_contract@1",
            enablement_rules_version="enablement_rules@1",
            dimension_weights={DimensionId.SKILLS: 0.10},
            enabled_dimensions=(DimensionId.SKILLS,),
        )


def test_loaded_match_config_carries_the_matching_contract_version() -> None:
    weights = Path(__file__).parents[4] / "config" / "match_weights.yaml"

    config = load_match_config(_CONFIG, weights)

    assert config.matching_contract_version == "matching_contract@1"
    assert config.enablement_rules_version == "enablement_rules@1"
    assert config.dimension_weights[DimensionId.SKILLS] == Decimal("0.30")
    with pytest.raises(ValidationError):
        MatchConfig.model_validate(
            {
                "matching_contract_version": "matching_contract@1",
                "enablement_rules_version": "enablement_rules@1",
                "dimension_weights": {"unknown": Decimal("0.10")},
                "enabled_dimensions": ["unknown"],
            }
        )
