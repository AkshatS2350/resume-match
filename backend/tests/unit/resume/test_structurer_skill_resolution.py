from decimal import Decimal
from pathlib import Path

from resumematch.core.schemas.candidate import Provenance
from resumematch.resume.structure.skills import skill_item
from resumematch.skill.alias_loader import load_aliases
from resumematch.skill.normalizer import SkillNormalizer

_ROOT = Path(__file__).parents[4]
_NORMALIZER = SkillNormalizer(load_aliases(_ROOT / "ontology" / "skills.yaml"))
_PROVENANCE = Provenance(section_id="skills", block_ids=("1:1",), start_offset=0, end_offset=2)


def test_equivalent_skill_surfaces_preserve_surface_and_share_canonical_id() -> None:
    items = tuple(
        skill_item(
            item_id=f"skill-{index}",
            surface=surface,
            normalizer=_NORMALIZER,
            confidence=Decimal("0.80"),
            confidence_inputs=("base",),
            provenance=_PROVENANCE,
        )
        for index, surface in enumerate(("JS", "JavaScript", "Javascript"), start=1)
    )

    assert tuple(item.surface for item in items) == ("JS", "JavaScript", "Javascript")
    assert {item.canonical_skill_id for item in items} == {"javascript"}


def test_unrecognized_skill_preserves_its_surface_and_unmapped_identifier() -> None:
    item = skill_item(
        item_id="skill-1",
        surface="Invented Tool",
        normalizer=_NORMALIZER,
        confidence=Decimal("0.80"),
        confidence_inputs=("base",),
        provenance=_PROVENANCE,
    )

    assert item.surface == "Invented Tool"
    assert item.canonical_skill_id == "unmapped:invented tool"
