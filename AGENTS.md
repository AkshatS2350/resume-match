# ResumeMatch implementation steering

## Source of truth

`.kiro/specs/resumematch/requirements.md` →
`.kiro/specs/resumematch/design.md` →
`.kiro/specs/resumematch/tasks.md` → code. A task cannot override requirements or
design. Amend the specification before changing observable behaviour.

## Scope

Implement only the active task or explicit task batch. Do not begin adjacent tasks, future milestones, or the next major task without instruction.

## Privacy

Never persist Candidate_Data, log raw resume text or PII, or route candidate-derived cloud egress outside `LLM_Gateway`. Do not weaken import-linter, AST, host allow-list, projection, or sanitization controls to pass tests. Sanitization failures fail closed.

## Determinism and truthfulness

LLMs never influence scores, Evidence_Level, Confidence_Value, dimensions, or Match_Class. Use the deterministic mechanisms in `design.md`. Never fabricate skills, experience, employers, projects, certifications, achievements, responsibilities, or numeric impact.

## Architecture

Preserve dependency layering, the two network enclaves, `Job_Source` and `LLM_Provider` interfaces, config-driven rubrics, generic scoring, and deterministic validators. No domain-specific scoring branches. Additional rubrics require an explicit task and must be schema-conforming configuration.

### Layer order and egress enclaves

The dependency order is lowest first: `core` → `skill` → `resume` → `privacy` →
`llm` → `rubric` → `job` → `matching` → `coach` → `api`. A lower layer importing a
higher layer is a build failure. `llm.providers` is the LLM-provider egress enclave;
`job.adapters` is the job-source network enclave. No other module may perform outbound
network I/O or reference the `LLM_Provider` interface.

### Determinism and failure handling

Inject a `Clock`; use `Decimal` with explicit rounding; iterate in sorted order; never
use `round()`, floats, wall-clock reads, random values, or filesystem-order iteration
in deterministic scoring and matching paths. Validation, sanitization, consent,
boundary, and configuration failures fail closed: transmit nothing, persist nothing,
and return the named safe error.

### CI gates

The mandatory no-override jobs are `privacy`, `pii-gates`, `boundary`,
`reqx-accuracy`, `fabrication`, and `determinism`. Do not weaken their tests, import
contracts, AST checks, host allow-lists, projections, or sanitization controls.

## v1 prohibitions

No authentication, accounts, candidate history, vector DB, embeddings, microservices, queues, multi-worker in-memory sessions, multiple cloud LLM providers, LinkedIn/Indeed scraping, auto-apply, native apps, or OCR without a specification amendment.

## Engineering discipline

Tests are part of each task. Run relevant tests before completion; do not weaken failing tests. Complete spikes as measured decisions/ADRs, not retained production code. Preserve stable IDs, document conflicts, and stop before the next major task unless explicitly instructed.
