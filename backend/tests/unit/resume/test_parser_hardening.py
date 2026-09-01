import pytest

from resumematch.core.errors import ErrorCode, PipelineError
from resumematch.resume.extract.hardening import parse_docx_xml


def test_xml_external_entity_is_mapped_to_safe_extraction_failure() -> None:
    payload = b'<!DOCTYPE x [<!ENTITY secret SYSTEM "file:///etc/passwd">]><x>&secret;</x>'
    with pytest.raises(PipelineError) as raised:
        parse_docx_xml(payload)
    assert raised.value.code is ErrorCode.EXTRACTION_FAILED
    assert "passwd" not in str(raised.value)
