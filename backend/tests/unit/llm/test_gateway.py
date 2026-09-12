from dataclasses import FrozenInstanceError

import pytest

from resumematch.llm.budget import PayloadBudget
from resumematch.llm.gateway import (
    AdmissionDenial,
    AdmissionDenied,
    AdmittedPayload,
    admit,
    admit_payload,
)
from resumematch.llm.projection import FieldPath


def test_unknown_operation_is_denied_without_a_provider() -> None:
    result = admit("unknown")

    assert result == AdmissionDenied(AdmissionDenial.UNKNOWN_OPERATION)


def test_admitted_payload_is_typed_frozen_and_rejects_extra_fields() -> None:
    result = admit_payload(
        {FieldPath("/summary"): "exact sanitized value"},
        frozenset(),
        PayloadBudget(1_000, "budget_priority@1"),
    )

    assert isinstance(result, AdmittedPayload)
    assert result.payload == {FieldPath("/summary"): "exact sanitized value"}
    with pytest.raises(FrozenInstanceError):
        result.payload = {}  # type: ignore[misc]
    with pytest.raises(TypeError):
        AdmittedPayload(payload={}, reduction=result.reduction, unexpected=True)  # type: ignore[call-arg]
