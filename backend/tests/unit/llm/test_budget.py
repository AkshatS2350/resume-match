"""Canonical value-bearing LLM payload budgeting."""

from pathlib import Path

from resumematch.llm.budget import (
    BudgetExceeded,
    PayloadBudget,
    load_budget_priority,
    reduce_to_budget,
)


def test_reducer_measures_canonical_values_and_preserves_included_values() -> None:
    payload = {"/required": "same", "/optional": "long optional value"}

    result = reduce_to_budget(
        payload, frozenset({"/required"}), PayloadBudget(30, "budget_priority@1")
    )

    assert result.included_payload == {"/required": "same"}
    assert result.dropped_paths == ("/optional",)
    assert result.rendered_character_count == len(b'{"/required":"same"}')


def test_reducer_returns_budget_exceeded_without_dropping_required_values() -> None:
    result = reduce_to_budget(
        {"/required": "cannot change"},
        frozenset({"/required"}),
        PayloadBudget(1, "budget_priority@1"),
    )

    assert isinstance(result, BudgetExceeded)
    assert result.required_paths == ("/required",)
    assert result.required_rendered_length > result.budget_limit


def test_reducer_drops_optional_paths_in_configured_priority_order() -> None:
    payload = {
        "/required": "keep",
        "/achievements/0": "drop first",
        "/summary": "drop second",
    }

    result = reduce_to_budget(
        payload,
        frozenset({"/required"}),
        PayloadBudget(20, "budget_priority@1"),
        ("/achievements/*", "/summary"),
    )

    assert result.included_payload == {"/required": "keep"}
    assert result.dropped_paths == ("/achievements/0", "/summary")


def test_reducer_normalizes_input_order() -> None:
    budget = PayloadBudget(30, "budget_priority@1")
    first = reduce_to_budget({"/b": "two", "/a": "one"}, frozenset(), budget)
    second = reduce_to_budget({"/a": "one", "/b": "two"}, frozenset(), budget)

    assert first == second


def test_budget_priority_is_loaded_from_the_versioned_config() -> None:
    root = Path(__file__).resolve().parents[4]

    priority = load_budget_priority(root / "config" / "llm_budget_priority.yaml")

    assert priority.budget == PayloadBudget(10000, "budget_priority@1")
    assert priority.optional_path_priority[0].pattern == "/achievements/*"
    assert priority.optional_path_priority[0].index_direction == "descending"


def test_reducer_drops_array_items_with_descending_indexes_first() -> None:
    payload = {"/required": "keep", "/achievements/0": "first", "/achievements/1": "second"}

    result = reduce_to_budget(
        payload,
        frozenset({"/required"}),
        PayloadBudget(20, "budget_priority@1"),
        ("/achievements/*",),
    )

    assert result.dropped_paths == ("/achievements/1", "/achievements/0")
