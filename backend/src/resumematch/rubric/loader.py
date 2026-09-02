"""Read-only, deterministic loading and validation of declarative role rubrics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from resumematch.core.schemas.rubric import RoleRubric
from resumematch.skill.alias_loader import AliasSet


class RubricLoadError(ValueError):
    """A requested rubric was unavailable because its configuration failed validation."""


@dataclass(frozen=True)
class RubricLoadResult:
    loaded: tuple[RoleRubric, ...]
    failures: tuple[str, ...]

    def require(self, role_id: str, domain_id: str, seniority_id: str) -> RoleRubric:
        key = (role_id, domain_id, seniority_id)
        for rubric in self.loaded:
            if (rubric.role_id, rubric.domain_id, rubric.seniority_id) == key:
                return rubric
        raise RubricLoadError(f"RUBRIC_UNAVAILABLE: {'.'.join(key)}")


def load_rubrics(directory: Path, aliases: AliasSet) -> RubricLoadResult:
    """Validate every configured file while retaining unrelated valid rubrics."""

    loaded: list[RoleRubric] = []
    failures: list[str] = []
    identities: dict[tuple[str, str, str], Path] = {}
    valid_skills = {entry.identifier for entry in aliases.entries}
    for path in sorted(directory.glob("*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            rubric = RoleRubric.model_validate(raw)
        except (OSError, ValidationError, yaml.YAMLError) as error:
            failures.append(f"{path}: {error}")
            continue
        weight_total = sum(category.weight for category in rubric.categories)
        if weight_total != 100:
            failures.append(f"{path}: category weights must sum to 100")
            continue
        unknown_skills = sorted(
            signal.canonical_skill_id
            for category in rubric.categories
            for signal in category.signals
            if signal.type == "skill"
            and signal.canonical_skill_id is not None
            and signal.canonical_skill_id not in valid_skills
        )
        if unknown_skills:
            failures.append(f"{path}: unknown canonical skill {unknown_skills[0]}")
            continue
        identity = (rubric.role_id, rubric.domain_id, rubric.seniority_id)
        existing = identities.get(identity)
        if existing is not None:
            failures.append(f"{existing} and {path}: duplicate rubric identity {identity}")
            continue
        identities[identity] = path
        loaded.append(rubric)
    return RubricLoadResult(tuple(loaded), tuple(failures))
