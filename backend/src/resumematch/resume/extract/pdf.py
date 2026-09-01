"""Deterministic local PDF text extraction."""

from decimal import Decimal
from pathlib import Path
from typing import Any

import pdfplumber

from resumematch.core.config import load_config
from resumematch.core.schemas.extracted_text import ExtractedBlock, ExtractedText
from resumematch.resume.extract.normalize import normalize

_CONFIG_PATH = Path(__file__).resolve().parents[5] / "config" / "extraction.yaml"
_COLUMN_GAP_FRACTION = load_config(_CONFIG_PATH, decimal_keys=frozenset({"column_gap_fraction"}))[
    "column_gap_fraction"
]
assert isinstance(_COLUMN_GAP_FRACTION, Decimal)


def _line_segments(words: list[dict[str, Any]], width: float) -> list[tuple[float, str]]:
    segments: list[list[dict[str, Any]]] = []
    previous_x1: float | None = None
    threshold = float(Decimal(str(width)) * _COLUMN_GAP_FRACTION)
    for word in sorted(words, key=lambda item: float(item["x0"])):
        if previous_x1 is None or float(word["x0"]) - previous_x1 > threshold:
            segments.append([])
        segments[-1].append(word)
        previous_x1 = float(word["x1"])
    return [
        (float(segment[0]["x0"]), " ".join(str(word["text"]) for word in segment))
        for segment in segments
    ]


def _page_blocks(page: Any, page_number: int) -> list[tuple[str, int | None]]:
    lines: dict[float, list[dict[str, Any]]] = {}
    for word in page.extract_words():
        lines.setdefault(round(float(word["top"]), 1), []).append(word)
    ordered = [
        (top, _line_segments(words, float(page.width))) for top, words in sorted(lines.items())
    ]
    column_start = next(
        (index for index, (_, segments) in enumerate(ordered) if len(segments) == 2), None
    )
    if column_start is None:
        return [(text, None) for _, segments in ordered for _, text in segments]
    prefix: list[tuple[str, int | None]] = [
        (text, None) for _, segments in ordered[:column_start] for _, text in segments
    ]
    split = sum(item[0] for item in ordered[column_start][1]) / 2
    body = ordered[column_start:]
    left: list[tuple[str, int | None]] = [
        (text, 0) for _, segments in body for x, text in segments if x < split
    ]
    right: list[tuple[str, int | None]] = [
        (text, 1) for _, segments in body for x, text in segments if x >= split
    ]
    return prefix + left + right


def extract_pdf(path: Path) -> ExtractedText:
    blocks: list[ExtractedBlock] = []
    texts: list[str] = []
    pages_with_text: list[int] = []
    with pdfplumber.open(path) as document:
        for page_number, page in enumerate(document.pages, start=1):
            page_blocks = _page_blocks(page, page_number)
            text = normalize("\n".join(item[0] for item in page_blocks))
            if len(text.strip()) >= 10:
                pages_with_text.append(page_number)
            if not text:
                continue
            for ordinal, (raw, column) in enumerate(page_blocks, start=1):
                block_text = normalize(raw)
                if not block_text:
                    continue
                start = sum(len(item) + 1 for item in texts)
                texts.append(block_text)
                blocks.append(
                    ExtractedBlock(
                        block_id=f"{page_number}:{ordinal}",
                        section_id="preamble",
                        page=page_number,
                        start_offset=start,
                        end_offset=start + len(block_text),
                        text=block_text,
                        layout_kind="paragraph",
                        column_index=column,
                    )
                )
        return ExtractedText(
            text="\n".join(texts),
            blocks=tuple(blocks),
            page_count=len(document.pages),
            pages_with_text_layer=tuple(pages_with_text),
            extractor_version="pdfplumber@0.11.6",
        )
