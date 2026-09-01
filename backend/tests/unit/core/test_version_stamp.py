import pytest
from pydantic import ValidationError

from resumematch.core.schemas.version_stamp import VersionStamp


def test_version_stamp_has_all_design_fields() -> None:
    fields = set(VersionStamp.model_fields)
    expected = {
        "schema_version",
        "engine_version",
        "rubric_id",
        "rubric_version",
        "rubric_status",
        "alias_file_version",
        "evidence_multiplier_version",
        "match_weight_version",
        "threshold_version",
        "confidence_weight_version",
        "pattern_set_version",
        "delimitation_version",
        "relevance_rule_version",
    }
    assert expected <= fields


def test_version_stamp_is_frozen_and_requires_nonoptional_fields() -> None:
    with pytest.raises(ValidationError):
        VersionStamp(schema_version="x")
