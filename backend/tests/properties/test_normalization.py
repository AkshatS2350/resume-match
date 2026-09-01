from hypothesis import given
from hypothesis import strategies as st

from resumematch.resume.extract.normalize import normalize


@given(st.text())
def test_normalization_is_idempotent(value: str) -> None:
    assert normalize(normalize(value)) == normalize(value)


def test_normalization_removes_prohibited_forms() -> None:
    result = normalize("ﬁ\u00a0A\r\nB   C\n\n\nD\u2014E")
    assert result == "fi A\nB C\n\nD-E"
