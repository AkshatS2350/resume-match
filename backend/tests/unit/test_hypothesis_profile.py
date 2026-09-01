from hypothesis import settings


def test_committed_hypothesis_profile_is_active() -> None:
    assert settings().derandomize is True
    assert settings().max_examples >= 100
