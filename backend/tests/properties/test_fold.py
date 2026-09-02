from hypothesis import given
from hypothesis import strategies as st

from resumematch.skill.fold import fold


# Feature: resumematch, Property 7: skill folding is idempotent.
@given(st.text())
def test_fold_is_idempotent(value: str) -> None:
    assert fold(fold(value)) == fold(value)


def test_fold_preserves_joined_plus_and_hash_skill_names() -> None:
    assert {fold(value) for value in ("C++", "c++", "C ++", "C  +  +")} == {"c++"}
    assert {fold(value) for value in ("C#", "c #")} == {"c#"}
