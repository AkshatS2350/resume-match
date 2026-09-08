import pytest
from pydantic import ValidationError

from resumematch.core.schemas.job import ExtractedRequirement


def _requirement(**changes: object) -> ExtractedRequirement:
    data: dict[str, object] = {
        "requirement_id": "req-1",
        "classification": "required",
        "low_confidence": False,
        "canonical_skill_id": "python",
        "unit_text": "Python",
        "start_offset": 0,
        "end_offset": 6,
        "unit_id": "unit-1",
        "excluded_category": None,
        "pattern_set_version": "patterns@1",
        "delimitation_version": "delim@1",
    }
    data.update(changes)
    return ExtractedRequirement.model_validate(data)


def test_requirement_round_trips_and_validates_offsets_and_exclusions() -> None:
    model = _requirement()
    assert ExtractedRequirement.model_validate_json(model.model_dump_json()) == model
    with pytest.raises(ValidationError, match="end_offset"):
        _requirement(end_offset=0)
    assert _requirement(excluded_category="visa_status").excluded_category == "visa_status"
    with pytest.raises(ValidationError):
        _requirement(excluded_category="other")
