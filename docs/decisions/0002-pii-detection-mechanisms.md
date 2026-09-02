# 0002 — PII detection mechanisms

## Decision

Use deterministic category patterns together with Presidio Analyzer backed by the
version-pinned `en_core_web_sm` spaCy NER model. The detector runs both mechanisms
over every candidate span and takes their union; it does not short-circuit after a
pattern match.

## Measurement

The synthetic labeled corpus contains 20 person-name and 20 postal-address instances.
The measurement used the category patterns and Presidio 2.2.362 with
`en_core_web_sm` 3.8.0. A label is recalled only when one result covers its full
zero-based, exclusive range.

| category | recall | precision | deterministic results | Presidio results |
| --- | ---: | ---: | ---: | ---: |
| person name | 1.00 (20/20) | 1.00 | 20 | 20 `PERSON` |
| postal address | 1.00 (20/20) | 1.00 | 20 | 0 `LOCATION` |

The chosen minimum classification-confidence floor is **0.80**. This corpus did not
exercise a below-floor finding, so its measured fail-safe-redaction cost is zero. The
configuration and sanitizer tasks must add a boundary fixture before treating that
figure as a production baseline.

## Outcome

The hard-category recall gate is a **go** on this synthetic pre-implementation corpus.
No second NER model or name gazetteer is selected at this point. The retained-field
adversarial cases (`Morgan Stanley`, `Ernst & Young`, and `Johns Hopkins`) and the
person name inside a project description remain required regression cases for the
Sanitizer's precedence rules.
