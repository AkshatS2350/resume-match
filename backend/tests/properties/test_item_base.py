from decimal import Decimal

import pytest
from pydantic import ValidationError

from resumematch.core.schemas.candidate import ItemBase, Provenance


def _provenance() -> Provenance:
    return Provenance(
        section_id="experience",
        block_ids=("block-1",),
        start_offset=0,
        end_offset=12,
    )


def test_extracted_item_requires_provenance_and_two_decimal_confidence() -> None:
    with pytest.raises(ValidationError, match="provenance"):
        ItemBase(
            item_id="item-1",
            origin="extracted",
            extraction_confidence=Decimal("0.80"),
            confidence_inputs=("heading_matched",),
            provenance=None,
            source_text="source text",
        )
    with pytest.raises(ValidationError, match="two decimal"):
        ItemBase(
            item_id="item-1",
            origin="extracted",
            extraction_confidence=Decimal("0.801"),
            confidence_inputs=(),
            provenance=_provenance(),
            source_text="source text",
        )


def test_user_provided_item_has_no_provenance_and_is_exactly_confident() -> None:
    item = ItemBase(
        item_id="item-1",
        origin="user_provided",
        extraction_confidence=Decimal("1.00"),
        confidence_inputs=(),
        provenance=None,
        source_text="source text",
    )
    assert item.extraction_confidence == Decimal("1.00")
