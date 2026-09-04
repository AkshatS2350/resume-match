from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from resumematch.privacy.detectors.rules import Detection


def test_resolve_spans_unions_transitive_overlaps_and_keeps_the_best_category() -> None:
    from resumematch.privacy.spans import resolve_spans

    resolved = resolve_spans(
        (
            Detection("email", 0, 4, Decimal("0.70")),
            Detection("person_name", 3, 7, Decimal("0.91")),
            Detection("telephone", 6, 10, Decimal("0.80")),
        )
    )

    assert resolved == (Detection("person_name", 0, 10, Decimal("0.91")),)


def test_resolve_spans_breaks_equal_confidence_ties_by_category() -> None:
    from resumematch.privacy.spans import resolve_spans

    resolved = resolve_spans(
        (
            Detection("telephone", 0, 4, Decimal("0.80")),
            Detection("email", 1, 5, Decimal("0.80")),
        )
    )

    assert resolved == (Detection("email", 0, 5, Decimal("0.80")),)


@given(
    st.lists(
        st.tuples(
            st.sampled_from(("email", "person_name", "telephone")),
            st.integers(min_value=0, max_value=20),
            st.integers(min_value=1, max_value=10),
            st.sampled_from((Decimal("0.70"), Decimal("0.80"), Decimal("0.91"))),
        ),
        min_size=1,
        max_size=12,
    )
)
def test_resolve_spans_preserves_every_detected_character_exactly_once(
    raw: list[tuple[str, int, int, Decimal]],
) -> None:
    from resumematch.privacy.spans import resolve_spans

    detections = tuple(
        Detection(category, start, start + length, confidence)
        for category, start, length, confidence in raw
    )
    resolved = resolve_spans(detections)

    assert all(left.end_offset <= right.start_offset for left, right in zip(resolved, resolved[1:]))
    for detection in detections:
        for offset in range(detection.start_offset, detection.end_offset):
            assert sum(item.start_offset <= offset < item.end_offset for item in resolved) == 1
