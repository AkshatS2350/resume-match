"""Deterministic alias resolution for profile and requirement text."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from resumematch.core.telemetry import emit_metric
from resumematch.skill.alias_loader import AliasSet
from resumematch.skill.fold import fold


@dataclass(frozen=True)
class CanonicalSkill:
    identifier: str
    display: str


def _discard_metric(_: str) -> None:
    """Default event sink; application wiring supplies the telemetry exporter."""


@dataclass
class SkillNormalizer:
    aliases: AliasSet
    review_list: list[CanonicalSkill] = field(default_factory=list)
    metric_emitter: Callable[[str], None] = _discard_metric

    def normalize(self, surface: str) -> CanonicalSkill:
        entry = self.aliases.by_folded_alias.get(fold(surface))
        if entry is not None:
            return CanonicalSkill(entry.identifier, entry.display)
        skill = CanonicalSkill(f"unmapped:{fold(surface)}", surface)
        self.review_list.append(skill)
        self.metric_emitter(emit_metric("unmapped_skill_total"))
        return skill

    def extract(self, text: str) -> tuple[CanonicalSkill, ...]:
        folded_text = fold(text)
        matches = [
            (alias, entry)
            for alias, entry in self.aliases.by_folded_alias.items()
            if alias and alias in folded_text
        ]
        matches.sort(key=lambda match: (-len(match[0]), match[1].identifier))
        result: list[CanonicalSkill] = []
        occupied: list[tuple[int, int]] = []
        for alias, entry in matches:
            start = folded_text.find(alias)
            end = start + len(alias)
            overlaps = any(
                start < existing_end and existing_start < end
                for existing_start, existing_end in occupied
            )
            if overlaps:
                continue
            occupied.append((start, end))
            result.append(CanonicalSkill(entry.identifier, entry.display))
        return tuple(result)
