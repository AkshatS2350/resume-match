"""The generic scorer registry has one stable slot per configured dimension."""

from resumematch.matching.contracts import DimensionId
from resumematch.matching.dimensions import SCORER_REGISTRY


def test_scorer_registry_keys_equal_the_seven_generic_dimension_ids() -> None:
    assert set(SCORER_REGISTRY) == set(DimensionId)
    assert tuple(SCORER_REGISTRY) == tuple(DimensionId)
    assert all(slot.dimension_id is dimension for dimension, slot in SCORER_REGISTRY.items())
