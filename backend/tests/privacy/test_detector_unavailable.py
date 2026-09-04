from datetime import UTC, datetime

import pytest

from resumematch.core.clock import FixedClock
from resumematch.core.errors import ErrorCode, PipelineError
from resumematch.core.session import SessionStore
from resumematch.privacy.detector import PIIDetector
from resumematch.privacy.detectors.rules import Detection


class RaisingMechanism:
    version = "ner@unavailable"

    def detect(self, text: str) -> tuple[Detection, ...]:
        raise RuntimeError("provider detail must not escape")


def test_detector_failure_is_a_safe_named_error_without_session_mutation() -> None:
    store = SessionStore(FixedClock(datetime(2026, 9, 2, tzinfo=UTC)))
    session = store.get(store.create())
    assert session is not None

    with pytest.raises(PipelineError) as error:
        PIIDetector((RaisingMechanism(),)).detect("candidate-derived text")

    assert error.value.code is ErrorCode.PII_DETECTION_UNAVAILABLE
    assert "provider detail" not in str(error.value)
    assert session.sanitized_resume is None
    assert session.sanitization_record is None


def test_detector_has_no_configuration_bypass_for_unavailable_mechanisms() -> None:
    assert tuple(PIIDetector.__dataclass_fields__) == ("mechanisms",)
