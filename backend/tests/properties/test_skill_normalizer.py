from pathlib import Path

from resumematch.skill.alias_loader import load_aliases
from resumematch.skill.normalizer import SkillNormalizer


def test_aliases_and_unmapped_surfaces_are_deterministic() -> None:
    aliases = load_aliases(Path(__file__).resolve().parents[3] / "ontology" / "skills.yaml")
    normalizer = SkillNormalizer(aliases)
    assert normalizer.normalize("PY").identifier == "python"
    unknown = normalizer.normalize("made up skill")
    assert unknown.identifier == "unmapped:made up skill"
    assert normalizer.review_list == [unknown]
