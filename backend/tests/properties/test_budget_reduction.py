"""Properties for deterministic, non-mutating canonical payload reduction."""

from hypothesis import given
from hypothesis import strategies as st

from resumematch.llm.budget import PayloadBudget, ReducedPayload, reduce_to_budget

_OPTIONAL_PATHS = ("/summary", "/achievements/0", "/projects/0/description")


@given(st.dictionaries(st.sampled_from(_OPTIONAL_PATHS), st.text(), min_size=1))
def test_reduction_is_repeatable_and_never_rewrites_included_values(
    payload: dict[str, str],
) -> None:
    budget = PayloadBudget(50, "budget_priority@1")
    priority = ("/achievements/*", "/projects/*/description", "/summary")

    first = reduce_to_budget(payload, frozenset(), budget, priority)
    second = reduce_to_budget(dict(reversed(tuple(payload.items()))), frozenset(), budget, priority)

    assert first == second
    if isinstance(first, ReducedPayload):
        for path, value in first.included_payload.items():
            assert value == payload[path]
