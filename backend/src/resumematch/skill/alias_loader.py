"""Versioned, deterministic skill-alias configuration loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from resumematch.skill.fold import fold


class AliasConfigError(ValueError):
    """Raised for an invalid or ambiguous skill ontology."""


@dataclass(frozen=True)
class SkillAlias:
    identifier: str
    display: str
    categories: tuple[str, ...]
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class AliasSet:
    version: str
    entries: tuple[SkillAlias, ...]
    by_folded_alias: dict[str, SkillAlias]


def load_aliases(path: Path) -> AliasSet:
    """Load a ``skills@1`` ontology, rejecting duplicate folded aliases."""

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != "skills@1":
        raise AliasConfigError(f"{path}: version")
    raw_entries = data.get("skills")
    if not isinstance(raw_entries, list):
        raise AliasConfigError(f"{path}: skills")
    entries: list[SkillAlias] = []
    by_alias: dict[str, SkillAlias] = {}
    for raw in raw_entries:
        if not isinstance(raw, dict):
            raise AliasConfigError(f"{path}: skill entry")
        identifier = raw.get("id")
        display = raw.get("display")
        categories = raw.get("categories")
        aliases = raw.get("aliases")
        if not (
            isinstance(identifier, str)
            and isinstance(display, str)
            and isinstance(categories, list)
            and categories
            and all(isinstance(category, str) for category in categories)
            and isinstance(aliases, list)
            and aliases
            and all(isinstance(alias, str) for alias in aliases)
        ):
            raise AliasConfigError(f"{path}: {identifier or 'skill'}")
        entry = SkillAlias(identifier, display, tuple(categories), tuple(aliases))
        for alias in entry.aliases:
            folded = fold(alias)
            existing = by_alias.get(folded)
            if existing is not None and existing.identifier != entry.identifier:
                raise AliasConfigError(
                    f"{path}: folded alias {folded!r} maps to "
                    f"{existing.identifier} and {entry.identifier}"
                )
            by_alias[folded] = entry
        entries.append(entry)
    return AliasSet("skills@1", tuple(entries), by_alias)
