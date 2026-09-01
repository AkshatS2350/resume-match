from __future__ import annotations

import re
import unicodedata

from hypothesis import given
from hypothesis import strategies as st

from resumematch.core.canonical_json import canonical_json, canonical_sha256


@given(st.dictionaries(st.text(min_size=1), st.integers(), min_size=1))
def test_key_order_does_not_change_bytes(value: dict[str, int]) -> None:
    assert canonical_json(value) == canonical_json(dict(reversed(tuple(value.items()))))


def test_nfc_equivalent_strings_have_same_bytes() -> None:
    composed = "é"
    decomposed = unicodedata.normalize("NFD", composed)
    assert canonical_json({"x": composed}) == canonical_json({"x": decomposed})


@given(st.dictionaries(st.text(min_size=1), st.integers()))
def test_hash_format(value: dict[str, int]) -> None:
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", canonical_sha256(value))
