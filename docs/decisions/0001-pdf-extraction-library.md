# 0001: PDF extraction library and reading order

**Status:** Accepted for M1 implementation

## Decision

Use `pdfplumber` for PDF extraction. The fixed column-gap threshold is **0.06 of page width** (for US Letter, 36.72 points). The implementation must use direct word boxes: form physical lines from word boxes, treat a line with two separated groups as the start of a two-column region, emit any preceding full-width lines first, then emit the left column top-to-bottom followed by the right column top-to-bottom. Table rows remain left-to-right. The threshold is a configuration constant; it is never tuned per document.

`python-docx` remains the DOCX path specified by D-36.

## Measurement

The initial literal x-midpoint clustering was run over all eleven synthetic fixtures. It preserved offset slices (28 blocks out of 28) but did **not** preserve the intended reading order for the two-column or table fixtures: header and column words were split into unrelated clusters. A direct word-box fallback with the fixed 0.06 gap preserves the intended order for the three layout-sensitive fixtures below.

| Fixture | Reading-order verdict | Offset fidelity |
| --- | --- | --- |
| `01-single-column.pdf` | Pass | 1/1 blocks reproduce their exact slice |
| `02-two-column.pdf` | Pass with selected direct word-box fallback; literal clustering failed | 3/3 |
| `03-table-based.pdf` | Pass with selected direct word-box fallback; literal clustering failed | 3/3 |
| `04-text-box.pdf` | Pass | 1/1 |
| `05-multi-page.pdf` | Pass | 5/5 |
| `06-missing-sections.pdf` | Pass | 1/1 |
| `07-duplicate-headings.pdf` | Pass | 2/2 |
| `08-unusual-headings.pdf` | Pass | 2/2 |
| `09-malformed-encoding.pdf` | Pass for reading order; text normalization is assessed separately | 1/1 |
| `10-image-only.pdf` | Pass: expected zero text blocks | 0/0 |
| `11-docx-resume.docx` | Pass through the `python-docx` path | 9/9 |

The resulting total is **28/28 blocks** whose recorded text exactly reproduces `extracted_text[start_offset:end_offset]`.

## Alternatives evaluated

PyMuPDF `get_text("text", sort=True)` visually retained two-column rows side by side rather than the required column-by-column order. It also introduces an AGPL/commercial-licensing decision for an open-source distribution, so it is not selected for v1.

The selected `pdfplumber` direct word-box fallback is pure Python, preserves the source-word geometry needed for provenance offsets, and avoids that licensing question. Task 9.3 will implement this measured ordering rule and its exact threshold.
