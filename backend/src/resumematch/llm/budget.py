"""Deterministic canonical-size budgeting for admitted, sanitized payload values."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

from resumematch.core.canonical_json import canonical_json
from resumematch.llm.projection import FieldPath, jsonpointer_sort_key

PayloadPath = FieldPath
type PayloadValue = (
    str | int | bool | None | tuple[PayloadValue, ...] | Mapping[str, PayloadValue]
)


@dataclass(frozen=True)
class PayloadBudget:
    """A versioned maximum canonical rendered-payload length."""

    maximum_rendered_characters: int
    version: str

    def __post_init__(self) -> None:
        if self.maximum_rendered_characters < 0:
            raise ValueError("maximum_rendered_characters must be non-negative")


@dataclass(frozen=True)
class BudgetPriority:
    """Config-backed omission ordering and its canonical payload budget."""

    budget: PayloadBudget
    optional_path_priority: tuple[PathPriority, ...]


@dataclass(frozen=True)
class PathPriority:
    pattern: PayloadPath
    index_direction: str | None


class _BudgetPriorityConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    version: str
    max_rendered_characters: int
    optional_path_priority: list[_PathPriorityConfig]


class _PathPriorityConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    pattern: str
    index_direction: str | None = None


class BudgetExceeded(BaseModel):
    """Required content cannot fit without violating the privacy contract."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    required_rendered_length: int
    budget_limit: int
    required_paths: tuple[PayloadPath, ...]
    budget_version: str


@dataclass(frozen=True)
class ReducedPayload:
    """Exact values retained after deterministic optional-path reduction."""

    included_payload: dict[PayloadPath, PayloadValue]
    dropped_paths: tuple[PayloadPath, ...]
    rendered_character_count: int
    budget_version: str
    reduction_trace: tuple[PayloadPath, ...]


def reduce_to_budget(
    payload: Mapping[PayloadPath, PayloadValue],
    required_paths: frozenset[PayloadPath],
    budget: PayloadBudget,
    optional_path_priority: tuple[PayloadPath, ...] = (),
) -> ReducedPayload | BudgetExceeded:
    """Keep exact approved values that fit; required paths always remain intact."""

    normalized = _normalized_payload(payload)
    required = tuple(sorted(required_paths.intersection(normalized), key=jsonpointer_sort_key))
    required_payload = {path: normalized[path] for path in required}
    required_length = _rendered_length(required_payload)
    if required_length > budget.maximum_rendered_characters:
        return BudgetExceeded(
            required_rendered_length=required_length,
            budget_limit=budget.maximum_rendered_characters,
            required_paths=required,
            budget_version=budget.version,
        )

    included = dict(normalized)
    optional = [path for path in normalized if path not in required_paths]
    ordered = _ordered_optional_paths(optional, optional_path_priority)
    dropped: list[PayloadPath] = []
    for path in ordered:
        if _rendered_length(included) <= budget.maximum_rendered_characters:
            break
        del included[path]
        dropped.append(path)
    return ReducedPayload(
        included_payload=dict(
            sorted(included.items(), key=lambda item: jsonpointer_sort_key(item[0]))
        ),
        dropped_paths=tuple(dropped),
        rendered_character_count=_rendered_length(included),
        budget_version=budget.version,
        reduction_trace=tuple(dropped),
    )


def load_budget_priority(path: Path) -> BudgetPriority:
    """Load the single versioned, declarative optional-path omission order."""

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    config = _BudgetPriorityConfig.model_validate(raw)
    if config.version != "budget_priority@1":
        raise ValueError(f"{path}: version")
    if any(not rule.pattern.startswith("/") for rule in config.optional_path_priority):
        raise ValueError(f"{path}: optional_path_priority")
    return BudgetPriority(
        budget=PayloadBudget(config.max_rendered_characters, config.version),
        optional_path_priority=tuple(
            PathPriority(FieldPath(rule.pattern), rule.index_direction)
            for rule in config.optional_path_priority
        ),
    )


def _normalized_payload(
    payload: Mapping[PayloadPath, PayloadValue],
) -> dict[PayloadPath, PayloadValue]:
    normalized: dict[PayloadPath, PayloadValue] = {}
    for path, value in payload.items():
        if not str(path).startswith("/"):
            raise ValueError("payload paths must be JSON Pointer paths")
        normalized[path] = value
    return normalized


def _ordered_optional_paths(
    paths: list[PayloadPath], priority: tuple[PayloadPath, ...]
) -> tuple[PayloadPath, ...]:
    ranks = {path: _priority_rank(path, priority, default=len(priority)) for path in paths}
    return tuple(
        sorted(paths, key=lambda path: (ranks[path], _descending_index_key(path, priority)))
    )


def _priority_rank(path: PayloadPath, priority: tuple[PayloadPath, ...], default: int) -> int:
    path_parts = str(path).split("/")
    for index, pattern in enumerate(priority):
        pattern_parts = str(pattern).split("/")
        pairs = zip(pattern_parts, path_parts, strict=True)
        if len(path_parts) == len(pattern_parts) and all(
            part == "*" or part == value for part, value in pairs
        ):
            return index
    return default


def _descending_index_key(
    path: PayloadPath, priority: tuple[PayloadPath, ...]
) -> tuple[int, tuple[str, ...]]:
    index = _priority_rank(path, priority, default=len(priority))
    pattern = priority[index] if index < len(priority) else None
    final = str(path).rsplit("/", 1)[-1]
    if pattern is not None and str(pattern).endswith("/*") and final.isdecimal():
        return (-int(final), jsonpointer_sort_key(path))
    return (0, jsonpointer_sort_key(path))


def _rendered_length(payload: Mapping[PayloadPath, PayloadValue]) -> int:
    return len(canonical_json(dict(payload)))
