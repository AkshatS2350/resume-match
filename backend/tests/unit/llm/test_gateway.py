from resumematch.llm.gateway import AdmissionDenial, AdmissionDenied, admit


def test_unknown_operation_is_denied_without_a_provider() -> None:
    result = admit("unknown")

    assert result == AdmissionDenied(AdmissionDenial.UNKNOWN_OPERATION)
