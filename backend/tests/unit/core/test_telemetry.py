import pytest

from resumematch.core.telemetry import emit_log, emit_metric, sanitize_exception


def test_allow_lists_reject_candidate_derived_metric_and_log_fields() -> None:
    with pytest.raises(ValueError, match="resume_text_total"):
        emit_metric("resume_text_total")
    with pytest.raises(ValueError, match="candidate_name"):
        emit_log(candidate_name="x")


def test_unknown_exception_messages_are_redacted() -> None:
    assert (
        sanitize_exception(ValueError("secret text"), "extract")
        == "ValueError at extract [redacted]"
    )
