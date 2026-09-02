# 0005 — First live job-source measurement

## Status

`completed_with_public_board_measurement_only`

## Measurement

On 2026-09-02, the public Greenhouse boards below were queried with the role-family
title filter used for the Task 33.1 spike. Counts are relevant postings followed by all
open postings returned by the board.

| board | relevant | all open postings |
| --- | ---: | ---: |
| Figma | 36 | 161 |
| Stripe | 173 | 592 |
| Datadog | 47 | 443 |
| Airtable | 3 | 16 |
| Cloudflare | 46 | 324 |
| **total** | **305** | **1,536** |

The observed mean is 61 relevant postings per organization. On this limited sample, two
organizations would project to at least 100 relevant postings; the range (3 to 173)
means that this is a planning estimate, not a coverage guarantee.

## Universal-search limitation

Adzuna was not measured. Its documented search endpoint requires an application ID and
application key, neither of which is configured for this repository. No Adzuna count is
inferred or represented as a live measurement. This decision reopens when project-owned
Adzuna credentials are supplied for a read-only measurement run.

## Recommendation and First Closed Loop effect

Greenhouse public boards remain the recommended first per-organization live source.
Adzuna remains the proposed first universal-search adapter, subject to OD-05 and the
credential-gated measurement above. Coverage is biased toward employers using
Greenhouse; any live coverage disclosure must state that limitation.

This limitation does **not** block the fixture-based First Closed Loop. The loop uses
only the version-controlled Fixture Job_Source_Adapter and requires no network or live
source credentials.
