"""Resolve overlapping removal-subject PII detections deterministically."""

from __future__ import annotations

from resumematch.privacy.detectors.rules import Detection


def resolve_spans(detections: tuple[Detection, ...]) -> tuple[Detection, ...]:
    """Union direct and transitive overlaps without losing any detected character."""

    ordered = sorted(
        detections,
        key=lambda item: (item.start_offset, item.end_offset, item.category),
    )
    resolved: list[Detection] = []
    group: list[Detection] = []
    group_end = 0
    for detection in ordered:
        if group and detection.start_offset >= group_end:
            resolved.append(_resolve_group(group))
            group = []
        group.append(detection)
        group_end = max(group_end, detection.end_offset)
    if group:
        resolved.append(_resolve_group(group))
    return tuple(resolved)


def _resolve_group(group: list[Detection]) -> Detection:
    selected = min(
        group,
        key=lambda item: (
            -item.confidence,
            item.category,
            item.start_offset,
            -item.end_offset,
        ),
    )
    return Detection(
        category=selected.category,
        start_offset=min(item.start_offset for item in group),
        end_offset=max(item.end_offset for item in group),
        confidence=selected.confidence,
    )
