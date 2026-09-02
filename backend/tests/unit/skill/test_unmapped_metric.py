import json

from resumematch.core.telemetry import METRIC_ALLOWLIST
from resumematch.skill.alias_loader import AliasSet
from resumematch.skill.normalizer import SkillNormalizer


def test_unmapped_surface_emits_one_allowlisted_value_free_metric() -> None:
    events: list[str] = []
    normalizer = SkillNormalizer(AliasSet("skills@1", (), {}), metric_emitter=events.append)
    normalizer.normalize("unmapped candidate-derived surface")
    assert "unmapped_skill_total" in METRIC_ALLOWLIST
    assert len(events) == 1
    assert json.loads(events[0]) == {"labels": {}, "name": "unmapped_skill_total", "value": 1}
