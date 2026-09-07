"""Skill-item construction through the injected deterministic normalizer."""

from decimal import Decimal

from resumematch.core.schemas.candidate import Provenance, SkillItem
from resumematch.skill.normalizer import SkillNormalizer


def skill_item(
    *,
    item_id: str,
    surface: str,
    normalizer: SkillNormalizer,
    confidence: Decimal,
    confidence_inputs: tuple[str, ...],
    provenance: Provenance,
) -> SkillItem:
    """Preserve a source surface while resolving its canonical skill identifier."""
    canonical = normalizer.normalize(surface)
    return SkillItem(
        item_id=item_id,
        origin="extracted",
        extraction_confidence=confidence,
        confidence_inputs=confidence_inputs,
        provenance=provenance,
        source_text=surface,
        surface=surface,
        canonical_skill_id=canonical.identifier,
    )
