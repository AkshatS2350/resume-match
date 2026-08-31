# Requirements Document

## Introduction

ResumeMatch is a privacy-first, open-source **job application decision engine**. A candidate uploads a resume, corrects the parsed result, selects a target domain and role, and receives a deterministic readiness assessment plus a ranked, explained set of real job postings classified as **Strong Apply**, **Stretch**, or **Skip**, with truthful application guidance.

ResumeMatch is not a resume grader. Its output is decision support: *which jobs am I competitive for, why, and what should I improve next?*

This document is the requirements baseline for the whole product, with each requirement mapped to a milestone so the design and task phases can sequence work. It is written for a downstream implementing agent, so acceptance criteria are testable and interfaces are named, but implementation choices (module layout, library selection, algorithm internals) are deliberately left to the design phase.

#### Source documents and precedence

| Source | Role |
|---|---|
| `ResumeMatch_Kiro_Planning_Handoff.md` | Authoritative. Wins all conflicts. |
| `ResumeMatch_Ideation.md` | Secondary. Broader ideation, used where it does not conflict. |

Where the two sources conflict, the resolution is recorded in [Resolved Source Conflicts](#resolved-source-conflicts). Where neither source settles a question, it is recorded in [Open Decisions](#open-decisions) rather than silently answered.

---

## Conventions

#### Modal verbs

| Verb | Meaning |
|---|---|
| **SHALL** | Mandatory. The mapped milestone is not complete until this is satisfied and covered by a test or inspectable artifact. |
| **SHOULD** | Desired. Omission requires a recorded decision, not silence. |
| **MAY** | Optional. Permitted, never assumed. |

Acceptance criteria default to SHALL. Criteria prefixed `[SHOULD]` or `[MAY]` are non-mandatory and use the corresponding verb.

#### Acceptance criteria form

Every criterion follows one EARS pattern: ubiquitous (`THE X SHALL …`), event-driven (`WHEN …`), state-driven (`WHILE …`), unwanted event (`IF … THEN …`), optional feature (`WHERE …`), or complex (clause order `WHERE → WHILE → WHEN/IF → THE → SHALL`).

#### Requirement metadata

Each requirement carries a metadata line:

`Milestone: Mn · Priority: P0|P1|P2 · Depends on: <requirement IDs>`

| Priority | Meaning |
|---|---|
| **P0** | Either of: (a) required for the First Closed Loop (see below); or (b) a non-negotiable safety or correctness constraint — privacy boundary, scoring determinism, evidence grounding, no fabrication — that must hold from the moment the feature it governs ships. |
| **P1** | Required for v1 public release. |
| **P2** | Post-v1 or explicitly deferred. |

A P0 requirement whose milestone falls outside M0–M8 is a safety constraint of kind (b): it is gated by its own milestone rather than by the First Closed Loop, and it does not pull its milestone into the loop. RM-LLM-002, RM-LLM-004, and RM-COACH-002 are the requirements in this category.

A bracketed criterion-level priority in a metadata line names the criterion whose priority differs from the requirement's leading priority — so `P0 (criterion 4: P1)` on RM-JOB-002 and RM-JOB-007 means criterion 4 is a P1 obligation while the remainder of the requirement is P0.

#### ID scheme

IDs are stable and never renumbered. Prefixes:

`RM-ING` upload/ingestion · `RM-PARSE` extraction and structuring · `RM-REV` profile review · `RM-PRIV` privacy and PII · `RM-EVID` evidence model · `RM-SKILL` skill normalization · `RM-RUB` rubric system · `RM-SCORE` readiness scoring · `RM-CONF` confidence · `RM-JOB` job ingestion · `RM-REQX` job requirement extraction · `RM-MATCH` matching and classification · `RM-COACH` application guidance · `RM-LLM` LLM layer · `RM-OPP` opportunity gain · `RM-UI` user interface · `RM-SESS` session and storage · `RM-API` API contracts · `RM-SEC` security · `RM-OBS` observability · `RM-PERF` performance · `RM-A11Y` accessibility · `RM-TEST` testing · `RM-EXT` extensibility · `RM-DEP` deployment.

#### The First Closed Loop

The first end-to-end product increment, and the boundary for P0:

```text
Upload resume → extract → structure → user corrects profile
→ sanitize → choose domain + role → deterministic readiness score
→ load controlled job set → normalize requirements → deterministic match
→ Strong Apply / Stretch / Skip with explanations
```

The "controlled job set" is the Fixture_Job_Set read through the Fixture Job_Source_Adapter. The First Closed Loop is executable end to end with the Fixture adapter alone and requires no live job source, no network access to an ATS or job API, and no Source_Registry entry for a live source. Shipping a live Job_Source_Adapter, live coverage breadth, live operational failure handling, and persistent live job caching are P1 obligations outside this loop.

Everything outside this loop is P1 or P2.

---

## Glossary

Named systems (used as the subject of SHALL statements):

- **ResumeMatch**: the complete product, frontend plus backend.
- **Web_Client**: the Next.js/React/TypeScript browser application.
- **Backend_API**: the FastAPI service exposing ResumeMatch HTTP endpoints.
- **Upload_Service**: the Backend_API component that accepts, validates, and hands off resume uploads.
- **Text_Extractor**: the component converting raw resume bytes into Extracted_Text.
- **Resume_Structurer**: the component converting Extracted_Text into a Structured_Resume.
- **Profile_Review_UI**: the Web_Client screen where the user inspects and corrects a Structured_Resume.
- **PII_Detector**: the component locating PII spans in Extracted_Text and Structured_Resume field values.
- **Sanitizer**: the component producing a Sanitized_Resume by applying PII_Detector findings and the configured retention policy.
- **Privacy_Inspector**: the Web_Client surface that displays what a Cloud_LLM_Request contains and what was removed.
- **Skill_Normalizer**: the component mapping surface skill strings to Canonical_Skill identifiers.
- **Rubric_Loader**: the component that reads, validates, and versions Role_Rubric configuration files.
- **Rubric_Engine**: the deterministic component computing Readiness_Score and category scores from a Candidate_Profile and a Role_Rubric.
- **Confidence_Calculator**: the deterministic component computing Confidence_Value and Confidence_Band.
- **Job_Source_Adapter**: any concrete implementation of the Job_Source interface (Greenhouse, Lever, Ashby, Adzuna, USAJobs, Fixture).
- **Source_Registry**: the configuration store listing which organizations/boards are polled for which Job_Source.
- **Job_Normalizer**: the component converting a raw posting from a Job_Source_Adapter into a Job_Posting.
- **Requirement_Extractor**: the component deriving required/preferred requirements from a Job_Posting description.
- **Matching_Engine**: the deterministic component computing a Match_Result for one Candidate_Profile and one Job_Posting.
- **Classifier**: the deterministic component assigning a Match_Class to a Match_Result.
- **Application_Coach**: the component producing per-job application guidance.
- **LLM_Gateway**: the Backend_API component that mediates all model calls, enforces the Cloud_Boundary, and validates model output.
- **LLM_Provider**: any concrete implementation of the provider interface behind LLM_Gateway.
- **Opportunity_Analyzer**: the component estimating Opportunity_Gain for missing skills.
- **Session_Store**: the mechanism holding per-analysis state for the duration of a Session.
- **Telemetry_Logger**: the component emitting logs, metrics, and traces.

Data terms:

- **Raw_Resume_Bytes**: the uploaded file exactly as received.
- **Extracted_Text**: the plain text recovered from Raw_Resume_Bytes, with layout metadata.
- **Structured_Resume**: the schema-conforming parse of Extracted_Text (skills, experience, education, projects, certifications, achievements), each item carrying Provenance and Extraction_Confidence.
- **Candidate_Profile**: the Structured_Resume after user correction, plus target constraints (domain, role, seniority, location, work mode), with Evidence_Level assigned to each signal.
- **Sanitized_Resume**: the Candidate_Profile with PII removed per the retention policy; the only candidate-derived payload permitted to cross the Cloud_Boundary.
- **Candidate_Evidence**: an individual, provenance-linked fact supporting a signal.
- **Evidence_Level**: the ordinal strength of a signal's support (see RM-EVID-001).
- **Provenance**: a pointer from a structured field to its location in Extracted_Text (section identifier plus character offsets).
- **Extraction_Confidence**: a deterministic per-field 0.0–1.0 value describing parse reliability.
- **Confidence_Value / Confidence_Band**: a deterministic 0.0–1.0 value and its ordinal band, attached to readiness and match outputs.
- **Role_Rubric**: a versioned configuration file defining categories, weights, and signals for one role at one seniority.
- **Readiness_Score**: the 0–100 deterministic score of a Candidate_Profile against a Role_Rubric.
- **Job_Posting**: the canonical normalized representation of one public job posting.
- **Hard_Requirement**: a job requirement whose absence disqualifies or heavily penalizes a candidate.
- **Preferred_Requirement**: a job requirement whose absence produces a minor penalty.
- **Requirement_Unit**: the delimited span of a Job_Posting description that is classified as a single requirement — one list item, or one sentence of non-list prose, split at the nearest clause boundary when longer than 400 characters — and from which at most one requirement per distinct Canonical_Skill is derived (RM-REQX-001 criterion 9).
- **Match_Result**: the deterministic per-job score, dimension breakdown, evidence, and gaps.
- **Match_Class**: one of `strong_apply`, `stretch`, `skip`.
- **Total_Relevant_Experience**: the total duration of the Candidate_Profile experience entries admitted by the configured relevance rule, counting any calendar period covered by two or more entries once, expressed in years to one decimal place (RM-MATCH-002 criterion 8). Consumed by the experience dimension of RM-MATCH-001 and by the seniority disqualification of RM-MATCH-002.
- **Permitted_Claim_Set**: the per-response set of Canonical_Skill identifiers, employer names, role titles, certification names, and numeric tokens that an Application_Coach response may reference, derived from the cited Candidate_Profile items (RM-COACH-002 criterion 1). A claim outside this set is a fabrication.
- **Canonical_Skill**: the normalized identifier for a skill and its aliases.
- **Cloud_Boundary**: the point at which data leaves ResumeMatch-controlled compute for a third-party model provider.
- **Cloud_LLM_Request**: any payload sent across the Cloud_Boundary.
- **Session**: one analysis workflow instance, identified by an opaque token, with a bounded lifetime.
- **Fixture_Job_Set**: a version-controlled, checked-in set of Job_Posting records used for the First Closed Loop and for tests.
- **Public_Job_Data**: job postings, source registry entries, and derived aggregates; contains no candidate data.
- **Candidate_Data**: any data derived from a user's resume or target constraints.

---

## Resolved Source Conflicts

These conflicts between the two source documents are resolved here. Downstream documents must not reopen them without amending this file.

**C-1 · Classification bands.** The handoff specifies three bands (Strong Apply / Stretch / Skip); the ideation document specifies four (adding "Apply"). **Resolution: three bands**, per RM-MATCH-003. The four-band variant is deferred as OD-08b.

**C-2 · Privacy modes.** The ideation document's "Mode A — Local Only" claims no resume-derived content leaves the device. That claim is not provable for the default architecture, in which a server-side FastAPI backend performs extraction, structuring, and sanitization. **Resolution:** the default deployment's honest guarantee is stated in RM-PRIV-001 and RM-PRIV-005 — resume files are not persistently stored by ResumeMatch servers, and Raw_Resume_Bytes are discarded after extraction. A genuine no-network-egress mode is conditional on the local-model milestone plus self-hosted deployment (RM-PRIV-006, M11) and must not be advertised before then.

**C-3 · Repository structure.** Handoff section 23 and ideation section 32 propose different layouts. **Resolution: not settled here.** This is a design-phase decision (OD-17). Requirements constrain module boundaries and contracts, not directory names.

**C-4 · Reference roles.** The two documents name the SWE and Marketing reference roles differently ("Backend / Software Engineer" vs "Backend Engineer — Intern / New Grad"; "Digital Marketing Analyst" vs "Performance Marketing Analyst — Entry"). **Resolution:** product owner decision OD-01 selects **Backend Engineer — Intern / New Grad** and **Performance Marketing Analyst — Entry**. The five roles are architecture-validation references, not a closed user-facing catalogue.

**C-5 · Evidence strength ladder.** The ideation document's 0–5 ladder is load-bearing for scoring, but neither document specifies how a level is inferred from resume text. **Resolution:** v1 reduces to four deterministically inferable levels plus a quantified-impact flag (RM-EVID-001). The reduction is recorded as AS-06 and the full ladder is deferred as OD-18.

**C-6 · Projection exactness versus request budget.** RM-PRIV-003 criterion 2 admits candidate-derived content across the Cloud_Boundary only as an exact projection of the Session's current Sanitized_Resume, with no truncated or otherwise derived value. RM-LLM-003 criterion 6 previously required the LLM_Gateway to truncate that projection when a configured request budget was exceeded. Truncating a candidate-derived value is a derived value, so the gateway could not satisfy both. **Resolution: exactness wins.** Budget reduction is achieved by omitting whole field paths and whole evidence items in a documented deterministic priority order, never by altering the value at an included field path, so every reduced request remains a valid projection under RM-PRIV-003 criterion 2. Where no eligible omission remains, the gateway returns `guidance_unavailable` rather than sending an altered value. Stated in RM-LLM-003 criterion 6 and RM-PRIV-003 criterion 12.

---

## Milestone Map

Milestones follow handoff section 27. Each requirement is mapped to the earliest milestone by which it must hold.

| Milestone | Theme | Requirements |
|---|---|---|
| **M0** | Repository, schemas, contracts, CI | RM-API-001, RM-SESS-001, RM-SEC-002, RM-SEC-003, RM-OBS-001, RM-OBS-002, RM-TEST-001, RM-DEP-001 |
| **M1** | Resume ingestion | RM-ING-001, RM-PARSE-001, RM-PARSE-002, RM-PRIV-001, RM-SEC-001, RM-PERF-001, RM-TEST-002 |
| **M2** | Resume structuring and correction | RM-PARSE-003, RM-PARSE-004, RM-PARSE-005, RM-REV-001, RM-A11Y-001 |
| **M3** | Privacy layer | RM-PRIV-002, RM-PRIV-003, RM-PRIV-004, RM-PRIV-005 |
| **M4** | Rubric engine | RM-EVID-001, RM-SKILL-001, RM-RUB-001, RM-RUB-002, RM-RUB-003, RM-SCORE-001, RM-SCORE-003, RM-EXT-001, RM-EXT-002 |
| **M5** | Candidate readiness | RM-SCORE-002, RM-CONF-001, RM-UI-001 |
| **M6** | Job ingestion | RM-JOB-001 … RM-JOB-008 |
| **M7** | Requirement extraction | RM-REQX-001, RM-REQX-002, RM-REQX-003 |
| **M8** | Matching and classification | RM-MATCH-001 … RM-MATCH-005 |
| **M9** | Job dashboard | RM-UI-002, RM-UI-003 |
| **M10** | LLM coach | RM-LLM-001 … RM-LLM-004, RM-COACH-001, RM-COACH-002 |
| **M11** | Local AI and self-host | RM-PRIV-006, RM-DEP-002 |
| **M12** | Opportunity gain | RM-OPP-001 |

The First Closed Loop spans the P0 requirements of M0–M8 and is executable with the Fixture Job_Source_Adapter reading the Fixture_Job_Set; it requires no live job source. RM-LLM-002, RM-LLM-004, and RM-COACH-002 are P0 safety constraints at M10 and are deliberately outside the loop, so "P0" alone must not be read as "build this first" — see the priority table in [Conventions](#conventions). Within M6, the P0 obligations are the canonical Job_Posting schema (RM-JOB-001), the Job_Source interface plus the Fixture adapter (RM-JOB-002), the Candidate_Data separation boundary (RM-JOB-007), and the prohibited-source restriction (RM-JOB-008). Live source integration, live coverage breadth, live operational failure handling, and persistent live job caching are P1 (RM-JOB-002 criterion 4, RM-JOB-003, RM-JOB-004 criteria 1, 2, 4, 5, and 6, RM-JOB-005, RM-JOB-006, RM-JOB-007 criterion 4), so a milestone-complete M6 is a v1 obligation rather than a First Closed Loop gate.

---

## Requirements

**1 · Resume Ingestion**

### Requirement 1: Resume upload and validation (RM-ING-001)

`Milestone: M1 · Priority: P0 · Depends on: RM-API-001`

**User Story:** As a new graduate, I want to upload my resume as a PDF or DOCX and be told immediately if the file is unusable, so that I am not left guessing why the analysis failed.

#### Acceptance Criteria

1. THE Upload_Service SHALL accept exactly two content types: `application/pdf` and `application/vnd.openxmlformats-officedocument.wordprocessingml.document`.
2. IF an upload declares or is detected as any other content type, THEN THE Upload_Service SHALL reject the upload with HTTP 415 and a machine-readable error code `UNSUPPORTED_FORMAT`.
3. THE Upload_Service SHALL determine the content type from the file's magic bytes rather than from the client-supplied filename extension alone.
4. IF an upload exceeds 10 MB, THEN THE Upload_Service SHALL reject the upload with HTTP 413 and error code `FILE_TOO_LARGE`, without reading the remainder of the request body into memory.
5. IF a PDF upload contains more than 15 pages, THEN THE Upload_Service SHALL reject the upload with error code `TOO_MANY_PAGES`.
6. THE Upload_Service SHALL exclude the client-supplied filename from all persisted records, log records, and response bodies.
7. THE Web_Client SHALL display the accepted formats and the maximum file size before the user selects a file.
8. IF an upload contains zero bytes, THEN THE Upload_Service SHALL reject the upload with error code `EMPTY_FILE`.

---

**2 · Text Extraction and Structuring**

### Requirement 2: Text extraction from PDF and DOCX (RM-PARSE-001)

`Milestone: M1 · Priority: P0 · Depends on: RM-ING-001`

**User Story:** As a candidate, I want my resume's text recovered accurately regardless of its layout, so that the analysis is based on what my resume actually says.

#### Acceptance Criteria

1. WHEN a valid PDF or DOCX upload is received, THE Text_Extractor SHALL produce Extracted_Text containing the document's textual content in a reading order.
2. THE Text_Extractor SHALL preserve, for each extracted text block, a section identifier and character offsets sufficient to support Provenance under RM-PARSE-005.
3. THE Text_Extractor SHALL recover text from multi-column layouts, tables, and text boxes in the fixture corpus defined by RM-TEST-002.
4. IF extraction produces fewer than 200 characters of text from a document of one or more pages, THEN THE Text_Extractor SHALL classify the result as an extraction failure and return error code `EXTRACTION_INSUFFICIENT_TEXT`.
5. IF the extraction library raises an unhandled error, THEN THE Text_Extractor SHALL return error code `EXTRACTION_FAILED` and a user-facing message that names the file type and suggests re-exporting the document as a text-based PDF.
6. THE Text_Extractor SHALL produce byte-identical Extracted_Text for repeated extraction of the same input file within one release version.
7. THE Text_Extractor SHALL normalize whitespace, ligatures, and non-breaking spaces to a documented canonical form.

---

### Requirement 3: Image-only PDF detection and safe failure (RM-PARSE-002)

`Milestone: M1 · Priority: P0 · Depends on: RM-PARSE-001`

**User Story:** As a candidate who exported a scanned resume, I want a clear explanation that my file cannot be read, so that I do not receive a silently empty or nonsensical profile.

#### Acceptance Criteria

1. WHEN a PDF contains no extractable text layer on any page, THE Text_Extractor SHALL classify the document as image-only and return error code `SCANNED_PDF_UNSUPPORTED`.
2. WHEN a PDF yields extractable text on fewer than half of its pages, THE Text_Extractor SHALL classify the document as partially image-only and return error code `SCANNED_PDF_PARTIAL` together with the list of affected page numbers.
3. IF a document is classified as image-only or partially image-only, THEN THE Backend_API SHALL stop the pipeline before Resume_Structurer runs and SHALL return no Structured_Resume.
4. WHEN the Web_Client receives `SCANNED_PDF_UNSUPPORTED` or `SCANNED_PDF_PARTIAL`, THE Web_Client SHALL display a message stating that the resume appears to be a scan or image, that optical character recognition is not supported, and that the user should upload a text-based PDF or DOCX.
5. THE Backend_API SHALL treat optical character recognition as out of scope for v1 and SHALL NOT silently substitute empty or partial content for an unreadable document.

---

### Requirement 4: Structured resume construction (RM-PARSE-003)

`Milestone: M2 · Priority: P0 · Depends on: RM-PARSE-001, RM-PARSE-004`

**User Story:** As a candidate, I want my resume turned into structured skills, experience, education, projects, and certifications, so that the system can reason about my background rather than about raw text.

#### Acceptance Criteria

1. WHEN Extracted_Text is available, THE Resume_Structurer SHALL produce a Structured_Resume conforming to the schema defined by RM-PARSE-004.
2. THE Resume_Structurer SHALL populate the sections `summary`, `skills`, `experience`, `education`, `projects`, `certifications`, and `achievements`, using an empty collection where a section is absent.
3. WHEN an experience entry contains a recognizable date range, THE Resume_Structurer SHALL record a start date, an end date or a present marker, and a computed duration in months.
4. IF a section heading is absent, duplicated, or unrecognized, THEN THE Resume_Structurer SHALL assign the affected content to an `unclassified` bucket that is visible in the Profile_Review_UI rather than discarding it.
5. THE Resume_Structurer SHALL produce identical Structured_Resume output for identical Extracted_Text input within one release version.
6. THE Resume_Structurer SHALL complete without an LLM_Provider call for all fixture inputs in RM-TEST-002.
7. `[MAY]` WHERE the LLM_Gateway is configured and the user has consented, THE Resume_Structurer MAY request bounded disambiguation of a single unclassified block, subject to RM-PRIV-003 and RM-LLM-002.

---

### Requirement 5: Structured resume schema and serialization round-trip (RM-PARSE-004)

`Milestone: M2 · Priority: P0 · Depends on: RM-API-001`

**User Story:** As an implementing contributor, I want one authoritative candidate schema, so that parsing, review, sanitization, and scoring cannot drift apart.

#### Acceptance Criteria

1. THE Backend_API SHALL define the Structured_Resume, Candidate_Profile, and Sanitized_Resume schemas as Pydantic models exported as JSON Schema.
2. THE Web_Client SHALL consume TypeScript types generated from the exported JSON Schema rather than hand-written duplicates.
3. FOR ALL valid Structured_Resume values, deserializing the serialized form SHALL produce a value equal to the original (round-trip property).
4. FOR ALL valid Candidate_Profile values, deserializing the serialized form SHALL produce a value equal to the original (round-trip property).
5. IF a payload fails schema validation at any module boundary, THEN THE Backend_API SHALL reject the payload with HTTP 422 and a field-level error list.
6. THE Backend_API SHALL version each schema and SHALL include the schema version in every response containing a Structured_Resume or Candidate_Profile.

---

### Requirement 6: Provenance and extraction confidence (RM-PARSE-005)

`Milestone: M2 · Priority: P0 · Depends on: RM-PARSE-003`

**User Story:** As a candidate, I want to see which part of my resume produced each extracted item, so that I can judge and correct mistakes.

#### Acceptance Criteria

1. THE Resume_Structurer SHALL attach Provenance to every skill, experience, education, project, certification, and achievement item, identifying the source section and character offsets in Extracted_Text.
2. THE Resume_Structurer SHALL attach an Extraction_Confidence value in the closed interval 0.0 to 1.0 to every item.
3. THE Resume_Structurer SHALL compute Extraction_Confidence from documented, deterministic inputs only, and SHALL record which inputs contributed to each value.
4. THE Resume_Structurer SHALL retain the original source text alongside the normalized value for every extracted item.
5. WHEN an item's Extraction_Confidence is below 0.6, THE Profile_Review_UI SHALL mark the item as needing review.
6. THE Backend_API SHALL exclude Extraction_Confidence values produced by an LLM_Provider from Extraction_Confidence fields.

---

### Requirement 7: Parsed profile review and correction (RM-REV-001)

`Milestone: M2 · Priority: P0 · Depends on: RM-PARSE-003, RM-PARSE-005`

**User Story:** As a career switcher, I want to correct what the parser got wrong before anything is scored, so that my results are not distorted by a parsing mistake.

#### Acceptance Criteria

1. THE Backend_API SHALL require a user-confirmed Candidate_Profile before Rubric_Engine or Matching_Engine executes.
2. THE Profile_Review_UI SHALL allow the user to add, edit, and remove items in every section of the Structured_Resume, including the `unclassified` bucket.
3. THE Profile_Review_UI SHALL allow the user to edit experience start dates, end dates, and titles, and SHALL recompute the displayed duration when a date is changed.
4. WHEN the user edits an item, THE Backend_API SHALL record the item's origin as `user_provided` and SHALL set its Extraction_Confidence to 1.0.
5. THE Profile_Review_UI SHALL display, for each item flagged under RM-PARSE-005 criterion 5, the original source text from the resume.
6. IF the user confirms a profile in which the `skills` and `experience` collections are both empty, THEN THE Web_Client SHALL warn that readiness scoring will produce a near-zero result and SHALL require an explicit confirmation to continue.
7. THE Profile_Review_UI SHALL preserve user corrections across a page reload within the same Session.

---

**3 · Privacy and PII**

### Requirement 8: Candidate data lifecycle and retention (RM-PRIV-001)

`Milestone: M1 (stages 1–3), M3 (full) · Priority: P0 · Depends on: RM-ING-001, RM-SESS-001`

**User Story:** As a privacy-conscious candidate, I want to know exactly what happens to each form of my data and for how long, so that I can trust the product without taking marketing claims on faith.

#### Acceptance Criteria

1. THE Backend_API SHALL treat candidate data as exactly seven distinct lifecycle stages: Raw_Resume_Bytes, Extracted_Text, Structured_Resume, Sanitized_Resume, Candidate_Profile, Session state, and permissible persistent data.
2. THE Backend_API SHALL release all references to Raw_Resume_Bytes before returning the response to the upload request that produced them.
3. THE Backend_API SHALL exclude Raw_Resume_Bytes from every persistent store, including databases, object stores, caches, and the filesystem, except for an operating-system-managed temporary file that is deleted before the upload response is returned.
4. WHERE the extraction library requires a filesystem path, THE Upload_Service SHALL write the temporary file with permissions restricted to the service account and SHALL delete the file in a guaranteed-cleanup construct that runs on both success and failure paths.
5. THE Backend_API SHALL hold Extracted_Text, Structured_Resume, and Candidate_Profile only in Session state.
6. THE Session_Store SHALL discard all Candidate_Data for a Session no later than 24 hours after the Session's last access.
7. THE Backend_API SHALL restrict persistent storage of Candidate_Data to the empty set, and SHALL restrict persistent storage to Public_Job_Data, Source_Registry entries, Role_Rubric files, skill ontology files, and privacy-safe telemetry as permitted by RM-OBS-001.
8. WHEN the user requests deletion of the current analysis, THE Backend_API SHALL discard all Session state for that Session and SHALL return confirmation.
9. THE Backend_API SHALL expose a documented statement of stages 1–7 that a reviewer can compare against the code, and RM-TEST-001 SHALL include a test asserting that no code path writes Raw_Resume_Bytes or Extracted_Text to a persistent store.

---

### Requirement 9: PII detection and category policy (RM-PRIV-002)

`Milestone: M3 · Priority: P0 · Depends on: RM-PARSE-003`

**User Story:** As a privacy-conscious candidate, I want direct identifiers removed from anything sent to a cloud model, while the career evidence that makes scoring useful is retained.

#### Acceptance Criteria

1. THE PII_Detector SHALL record every detected span as a zero-based start offset, an exclusive end offset, exactly one category drawn from the policy table below, and a classification confidence in the closed interval 0.00 to 1.00; WHEN removal-subject detected spans overlap directly or transitively, THE PII_Detector SHALL treat them as one connected overlap group, replace that group with one resolved span covering the union of every character range in the group, and assign it the category of the contributing detection with the highest classification confidence; WHEN contributing detections tie on confidence, THE PII_Detector SHALL select the category by lexicographically ascending category identifier and, if still tied, the contributing detection with the lower start offset and then the greater end offset. THE resolved output spans SHALL be pairwise non-overlapping, so that every redacted character belongs to exactly one resolved category and no character belonging to a detected removal span is lost because of overlap resolution.
2. THE PII_Detector SHALL detect and mark for removal: person names, email addresses, telephone numbers, postal addresses, personal profile URLs including LinkedIn and GitHub, personal website URLs, social handles, government or national identifiers, student or employee identifiers, dates of birth, and named references with their contact details; and THE PII_Detector SHALL exclude the placeholder tokens defined in criterion 9 from detection, so that a detection pass over a Sanitized_Resume reports no finding arising from a placeholder inserted by the Sanitizer.
3. THE Sanitizer SHALL retain, without redaction, the values of the fields whose policy-table default is Retain — employer names, educational institution names, certification names and issuing bodies, job titles, skill names, technology names, project descriptions, quantified impact statements, employment date ranges, and degree fields and levels — and SHALL apply that retention in precedence over criteria 2 and 5, so that a value in a Retain-default field that a detection mechanism reports as a person name, such as an employer name of the form "Morgan Stanley", is retained rather than removed; WHERE a span whose category carries a Remove default is detected inside a retained project description, THE Sanitizer SHALL replace that span under criterion 9 and SHALL retain the remainder of the description.
4. THE PII_Detector SHALL combine at least two independent detection mechanisms — deterministic pattern rules and a named-entity or PII-detection library — SHALL run every mechanism over every candidate span rather than stopping at the first mechanism that reports a finding, SHALL mark a span for removal when either mechanism identifies it subject to criterion 3, and SHALL set the span's classification confidence to the maximum of the classification confidences reported by the mechanisms that identified it.
5. WHERE a detected span lies outside the value of a Retain-default field, IF the span's classification confidence is below the configured minimum classification confidence, proposed as 0.80, THEN THE Sanitizer SHALL remove the span under criterion 9 and SHALL record the decision as a fail-safe redaction.
6. THE PII_Detector SHALL achieve a per-category recall of at least 0.95 for every category named in criterion 2 on the labeled privacy fixture corpus defined by RM-TEST-002, where per-category recall is the number of recalled labeled instances of that category divided by the total number of labeled instances of that category, a labeled instance counts as recalled when one reported span covers every character of that labeled instance and carries a policy-table default of Remove, and a reported span counts as a false positive for its category when the span overlaps no labeled instance of any Remove-default category; and THE PII_Detector SHALL report per-category precision on the same corpus, computed as the reported spans of that category that are not false positives divided by all reported spans of that category.
7. IF per-category recall for any category named in criterion 2 falls below the threshold in criterion 6, or the labeled privacy fixture corpus contains fewer than 20 labeled instances for any category named in criterion 2, or per-category precision for any category named in criterion 2 falls more than 0.05 below the figure recorded for the previous release, THEN RM-TEST-001 SHALL fail the build and SHALL report the affected category and the failing figure.
8. THE Backend_API SHALL express the policy table below as version-controlled configuration rather than as inline conditionals, and WHEN a category's default is changed from Retain to Remove or from Remove to Retain in that configuration, THE Sanitizer SHALL produce a correspondingly changed Sanitized_Resume for a fixture containing that category without any change to Python source files.
9. THE Sanitizer SHALL perform every removal as substitution of a per-category constant placeholder token whose form is independent of the removed value's content, length, and position; SHALL retain the containing field with the placeholder token as its value when the entire value of a field is removed, rather than deleting the field; and SHALL exclude the text of every removed span from the Sanitized_Resume in whole and in part, so that no fragment of a removed value is recoverable from any field path of the Sanitized_Resume.
10. IF either detection mechanism required by criterion 4 is unavailable or raises an error, THEN THE Sanitizer SHALL produce no Sanitized_Resume, SHALL write no sanitization record under RM-PRIV-003 criterion 6, SHALL return a failure to the calling component indicating that PII detection did not complete, and SHALL leave Session state unmodified.

**Policy table (v1 default):**

| Category | Default | Rationale |
|---|---|---|
| Person name, email, phone, postal address | Remove | Direct contact identifiers with no scoring value. |
| Personal URLs, social handles | Remove | Direct identifiers; repository content is not parsed in v1. |
| Government / student / employee IDs, date of birth | Remove | High-sensitivity identifiers with no scoring value. |
| Reference names and contact details | Remove | Third-party PII the candidate cannot consent on behalf of. |
| Employer name, institution name, certification issuer | **Retain** | Load-bearing career evidence; see tradeoff below. |
| Job title, skills, technologies, dates, degree | Retain | Core scoring inputs. |

**Stated tradeoff.** Employer and institution names are retained by default because domain exposure, industry signals, and role similarity in RM-MATCH-001 depend on them, and redacting them measurably degrades match quality. Retaining them raises re-identification risk: an uncommon employer-plus-institution-plus-date combination can identify an individual. The mitigation is disclosure (RM-PRIV-005), inspectability (RM-PRIV-004), and a user-facing opt-out is recorded as OD-04 rather than assumed.

---

### Requirement 10: Sanitization and the cloud boundary (RM-PRIV-003)

`Milestone: M3 · Priority: P0 · Depends on: RM-PRIV-002`

**User Story:** As a privacy-conscious candidate, I want a single enforced choke point for anything leaving the system, so that no future feature can accidentally leak my resume.

#### Acceptance Criteria

1. THE Backend_API SHALL route every Cloud_LLM_Request through the LLM_Gateway, and SHALL grant no component other than the LLM_Gateway access to the LLM_Provider interface or to any outbound transmission capability that crosses the Cloud_Boundary.
2. WHEN the LLM_Gateway receives a request containing candidate-derived content, THE LLM_Gateway SHALL admit that content for transmission only if it is a projection of the Session's current Sanitized_Resume, where a projection is a subset of that Sanitized_Resume's field paths in which every transmitted field path exists in that Sanitized_Resume and every transmitted value is exactly equal to the value at that path in that Sanitized_Resume; THE LLM_Gateway SHALL NOT admit a newly constructed, summarized, concatenated, transformed, truncated, or otherwise derived candidate-derived value.
3. IF candidate-derived content submitted to the LLM_Gateway fails the projection check in criterion 2, THEN THE LLM_Gateway SHALL reject the request without transmitting any part of the content, SHALL emit a telemetry event of severity `error` carrying only the offending field-path names, SHALL return a failure to the calling component indicating that unsanitized or unverifiable content was supplied, and SHALL leave Session state unmodified.
4. THE LLM_Gateway SHALL exclude Raw_Resume_Bytes and Extracted_Text from every Cloud_LLM_Request unconditionally, including when a calling component supplies them explicitly, and regardless of consent state, configuration, or provider identity.
5. WHILE a Session has no current Sanitized_Resume, THE Backend_API SHALL reject any request that would produce a Cloud_LLM_Request for that Session, SHALL transmit no candidate-derived content for that Session, and SHALL return a failure indicating that sanitization has not completed.
6. THE Sanitizer SHALL produce a Sanitized_Resume over which a re-run of the PII_Detector yields zero findings in removal categories under RM-PRIV-002, asserted by a test in RM-TEST-001 across every fixture in the privacy fixture corpus of RM-TEST-002, and THE Sanitizer SHALL be the only component permitted to write a Session's sanitization record, which identifies the Sanitized_Resume by content hash.
7. THE Sanitizer SHALL produce, when re-applied to a payload it has already sanitized, an output equal to that input, where equality is field-by-field equality of the serialized schema form defined by RM-API-001, asserted across every fixture in the privacy fixture corpus of RM-TEST-002.
8. THE Backend_API SHALL record in Session state, for every Cloud_LLM_Request, one manifest entry containing the request's field-path names, a content hash of the transmitted payload, and the transmission time; SHALL exclude candidate-derived values from every entry; SHALL retain at most the 200 most recent entries per Session, discarding oldest first; and SHALL discard the manifest together with the Session's Candidate_Data under RM-PRIV-001 criterion 6.
9. THE LLM_Gateway SHALL determine sanitized status solely from the Session's sanitization record written by the Sanitizer, and SHALL ignore any sanitization marker, flag, header, or attestation supplied by a calling component or contained in the request content.
10. IF the Candidate_Profile for a Session is modified after the Session's current Sanitized_Resume was produced, THEN THE Backend_API SHALL treat that Session as having no current Sanitized_Resume until the Sanitizer produces a new Sanitized_Resume and a new sanitization record.
11. RM-TEST-001 SHALL include a build-failing check that no Backend_API component other than the LLM_Gateway references the LLM_Provider interface or performs outbound transmission across the Cloud_Boundary, and a test in which a stub LLM_Provider records zero invocations for every request rejected under criteria 3, 5, or 10.
12. THE LLM_Gateway SHALL perform every budget-driven request reduction required by RM-LLM-003 criterion 6 by omitting entire field paths or entire evidence items and SHALL alter the value at no included field path, so that a request reduced for budget reasons remains a projection admissible under criterion 2 of this requirement and the budget rule of RM-LLM-003 criterion 6 does not conflict with it; and IF no eligible omission remains, THEN THE LLM_Gateway SHALL return a `guidance_unavailable` state under RM-LLM-003 criterion 6 rather than admit an altered candidate-derived value under criterion 2.

---

### Requirement 11: Privacy inspector (RM-PRIV-004)

`Milestone: M3 · Priority: P1 · Depends on: RM-PRIV-003`

**User Story:** As a privacy-conscious candidate, I want to read the exact payload before it goes to a cloud model, so that the privacy claim is verifiable rather than asserted.

The Privacy_Inspector presents two distinct artifacts, and must not conflate them. The **complete Session Sanitized_Resume** is what sanitization produced. The **pending request projection** is the candidate-derived projection contained in the pending Cloud_LLM_Request under RM-PRIV-003 criterion 2, possibly further reduced by whole-field omission for budget reasons under RM-LLM-003 criterion 6. Only the second artifact crosses the Cloud_Boundary.

#### Acceptance Criteria

1. WHILE a Cloud_LLM_Request is pending user consent, THE Privacy_Inspector SHALL display the list of field groups that will be transmitted and the list of categories that were removed.
2. THE Privacy_Inspector SHALL present as its primary "what will be sent" view the exact candidate-derived projection contained in the pending Cloud_LLM_Request, SHALL provide a control that reveals that projection in its complete serialized form, and SHALL NOT present the complete Session Sanitized_Resume as the payload that will be transmitted.
3. WHEN the user declines consent, THE Backend_API SHALL complete the readiness and matching workflow using deterministic components only and SHALL transmit no Cloud_LLM_Request for that Session.
4. THE Privacy_Inspector SHALL display the identity of the configured LLM_Provider and whether it executes locally or across the Cloud_Boundary.
5. THE Privacy_Inspector SHALL display the count of fail-safe redactions recorded under RM-PRIV-002 criterion 5.
6. THE Privacy_Inspector SHALL make the complete Session Sanitized_Resume viewable in a separate view labelled as the sanitization result held in Session state rather than as the transmitted payload, and SHALL distinguish that view from the pending request projection view of criterion 2.
7. THE Privacy_Inspector SHALL display every field path that is present in the Session's current Sanitized_Resume and absent from the pending request projection, and SHALL label each such field path as omitted because the requested operation does not require it or as omitted for budget reasons under RM-LLM-003 criterion 6, using the omission record that RM-LLM-003 criterion 6 makes available.

---

### Requirement 12: Honest privacy claims (RM-PRIV-005)

`Milestone: M3 · Priority: P0 · Depends on: RM-PRIV-001`

**User Story:** As a privacy-conscious candidate, I want claims I can hold the project to, so that I am not misled by an unprovable promise.

#### Acceptance Criteria

1. THE Web_Client SHALL state the privacy guarantee as "Resume files are not persistently stored by ResumeMatch servers."
2. THE Web_Client SHALL describe PII removal as a risk-reduction layer and SHALL state that a distinctive career history can remain identifying even after direct identifiers are removed.
3. THE Web_Client SHALL exclude from all user-facing copy any claim that resume content never leaves the user's device, unless the deployment satisfies RM-PRIV-006.
4. THE Web_Client SHALL exclude from all user-facing copy claims of anonymity, guaranteed de-identification, or that no data touches disk.
5. THE Web_Client SHALL disclose that employer names, institution names, and certification names are retained in the Sanitized_Resume, together with the reason.
6. RM-TEST-001 SHALL include a check over user-facing copy files that fails the build when a prohibited claim string from criteria 3 and 4 is present.

---

### Requirement 13: Local-only privacy mode (RM-PRIV-006)

`Milestone: M11 · Priority: P2 · Depends on: RM-PRIV-003, RM-LLM-001, RM-DEP-002`

**User Story:** As a privacy-conscious candidate, I want a deployment where no candidate-derived data leaves infrastructure I control, so that I can use the product on sensitive material.

#### Acceptance Criteria

1. WHERE ResumeMatch is deployed via the self-host Docker Compose configuration with a local LLM_Provider configured, THE Backend_API SHALL operate with zero outbound requests carrying Candidate_Data.
2. WHILE local-only mode is active, THE Web_Client SHALL display a persistent indicator naming the active mode and the local model endpoint.
3. WHILE local-only mode is active, IF a component attempts a request to a non-local LLM_Provider, THEN THE LLM_Gateway SHALL reject the request and SHALL emit a telemetry event of severity `error`.
4. THE Web_Client SHALL state that local-only mode's guarantee covers candidate data egress to model providers and SHALL state which non-candidate requests, such as job source polling, still occur.
5. RM-TEST-001 SHALL include an integration test that runs the full pipeline in local-only mode with outbound network access blocked and asserts successful completion.

---

**4 · Evidence and Skill Normalization**

### Requirement 14: Evidence strength model (RM-EVID-001)

`Milestone: M4 · Priority: P0 · Depends on: RM-REV-001, RM-PARSE-005`

**User Story:** As a candidate, I want a skill listed in a bullet point to count differently from a skill I merely listed, so that the score reflects demonstrated capability rather than keyword presence.

The ideation document's 0–5 ladder is reduced for v1 to four levels that can be inferred deterministically from the structure of the Candidate_Profile, plus one independent flag. The reduction is recorded as AS-06; the full ladder is OD-18.

| Level | Name | Deterministic rule |
|---:|---|---|
| 0 | Not present | The Canonical_Skill appears in no Candidate_Profile item. |
| 1 | Declared | The skill appears only in the `skills` or `summary` section. |
| 2 | Applied | The skill appears in a `projects`, `certifications`, `education`, or coursework item. |
| 3 | Professional | The skill appears in an `experience` item that has an employer and a date range. |

#### Acceptance Criteria

1. THE Rubric_Engine SHALL assign exactly one Evidence_Level from the set {0, 1, 2, 3} to every Canonical_Skill in the union of the skills resolved from the Candidate_Profile and the skills referenced by the Role_Rubric or Job_Posting under evaluation, SHALL assign Level 0 to every such skill that no Candidate_Profile item supports, and SHALL treat an item whose section is not named in the table above as supporting Level 1.
2. WHEN two or more Candidate_Profile items support one Canonical_Skill, THE Rubric_Engine SHALL evaluate the table rules once per supporting item and SHALL assign the numerically highest per-item level, so that Level 1 is assigned only when no supporting item qualifies at Level 2 or Level 3.
3. THE Rubric_Engine SHALL set the `quantified_impact` flag on a signal to true when and only when at least one supporting item's source text contains a numeral separated by at most one space character from a percent token, a currency symbol, or a unit token listed in a version-controlled unit list, SHALL exclude from this match any four-digit value in the range 1900 to 2100, any value located in the item's date fields, and any value forming a dotted version pattern, SHALL set the flag to false in all other cases, and SHALL NOT allow the flag's value to change the assigned Evidence_Level.
4. THE Rubric_Engine SHALL record, for every assigned Evidence_Level, the identifier and section identifier of each supporting Candidate_Profile item, which supporting item determined the assigned level, and, where `quantified_impact` is true, the identifier and character offsets of the matched quantity.
5. THE Rubric_Engine SHALL assign Evidence_Level using the rules in the table above and in criteria 1 through 4 and 8 through 10 only, without invoking an LLM_Provider.
6. FOR ALL Candidate_Profile values, repeated Evidence_Level and `quantified_impact` assignment SHALL produce identical results within one release version, including when the order of items within each Candidate_Profile section is permuted (determinism property).
7. THE Rubric_Engine SHALL exclude self-reported proficiency words drawn from a version-controlled exclusion list, such as "expert" or "advanced", from Evidence_Level and `quantified_impact` determination, so that deleting such a word from an item's text leaves the assigned Evidence_Level unchanged.
8. THE Rubric_Engine SHALL treat a Canonical_Skill as appearing in a Candidate_Profile item when the Skill_Normalizer resolves a token sequence in that item's skill-list, title, or description text to that Canonical_Skill, and SHALL exclude the employer-name, institution-name, and certification-issuer-name fields from this matching.
9. WHEN an `experience` item is evaluated, THE Rubric_Engine SHALL treat the item as supporting Level 3 only if the employer field contains at least two non-whitespace characters, the item resolves to both a start date and an end date where an end value of `present` resolves to the Session start date recorded with the Candidate_Profile, the resolved range spans at least one calendar month, and the skill mention occurs in the item's title or description text; otherwise THE Rubric_Engine SHALL treat the item as supporting Level 2 and SHALL record which condition was unmet.
10. IF a single `experience` item resolves to more than 20 distinct Canonical_Skills, THEN THE Rubric_Engine SHALL treat that item as supporting Level 2 rather than Level 3 for every skill it mentions and SHALL record the reason for the demotion on each affected signal.

---

### Requirement 15: Skill normalization (RM-SKILL-001)

`Milestone: M4 · Priority: P0 · Depends on: RM-PARSE-003`

**User Story:** As a candidate, I want "JS", "JavaScript", and "Javascript" treated as one skill, so that my resume is not penalized for wording.

#### Acceptance Criteria

1. THE Skill_Normalizer SHALL map a surface skill string to a Canonical_Skill identifier using a version-controlled alias file.
2. THE Skill_Normalizer SHALL define each Canonical_Skill entry with a canonical identifier, a display name, an alias list, and at least one category.
3. WHEN a surface string matches no alias, THE Skill_Normalizer SHALL emit an `unmapped` Canonical_Skill preserving the original string and SHALL record the string in a review list.
4. THE Skill_Normalizer SHALL be idempotent: normalizing an already-normalized Canonical_Skill SHALL return the same Canonical_Skill (idempotence property).
5. THE Skill_Normalizer SHALL apply case-insensitive and punctuation-insensitive matching, so that "C++", "c++", and "C ++" resolve to one identifier.
6. THE Skill_Normalizer SHALL apply the same alias file to Candidate_Profile skills and to Job_Posting requirements (confluence property: normalization is source-independent).
7. IF the alias file contains a duplicate alias mapped to two Canonical_Skill identifiers, THEN THE Skill_Normalizer SHALL fail to load and SHALL report both conflicting entries.
8. THE alias file SHALL be limited in v1 to the skills referenced by the reference Role_Rubric files plus their aliases, and SHALL NOT be expanded into a general ontology before the First Closed Loop is validated.

---

**5 · Role Rubrics and Readiness Scoring**

### Requirement 16: Rubric schema (RM-RUB-001)

`Milestone: M4 · Priority: P0 · Depends on: RM-SKILL-001, RM-EVID-001`

**User Story:** As a domain expert contributor, I want to describe how a role is evaluated in a configuration file, so that I can contribute without changing scoring code.

#### Acceptance Criteria

1. THE Rubric_Loader SHALL define one Role_Rubric schema shared by all domains and roles.
2. THE Role_Rubric schema SHALL support: role identifier, domain identifier, seniority identifier, rubric version, status, weighted categories, required signals, preferred signals, alternative signal groups, minimum Evidence_Level per signal, penalties, experience bands, education expectations, and certification expectations.
3. THE Rubric_Loader SHALL reject a Role_Rubric whose category weights do not sum to 100.
4. THE Rubric_Loader SHALL reject a Role_Rubric referencing a signal that resolves to no Canonical_Skill in the alias file, unless the signal is declared as a non-skill signal type.
5. THE Backend_API SHALL implement exactly one scoring code path shared by all Role_Rubric files, and SHALL contain no domain-specific or role-specific scoring branch.
6. FOR ALL valid Role_Rubric files, loading then serializing then loading SHALL produce an equivalent in-memory rubric (round-trip property).
7. THE Role_Rubric schema SHALL be expressed in YAML or JSON and SHALL be validated against an exported JSON Schema.

---

### Requirement 17: Rubric loading and validation (RM-RUB-002)

`Milestone: M4 · Priority: P0 · Depends on: RM-RUB-001`

**User Story:** As a domain expert contributor, I want a malformed rubric to be named and rejected at startup, so that a typo in my weights fails loudly instead of quietly scoring candidates against a broken rubric.

#### Acceptance Criteria

1. WHEN the Backend_API starts, THE Rubric_Loader SHALL validate every Role_Rubric file present and SHALL report each validation failure with the file path and the failing field.
2. IF any Role_Rubric file fails validation at startup, THEN THE Backend_API SHALL refuse to serve readiness scoring requests for that rubric and SHALL continue serving valid rubrics.
3. THE Rubric_Loader SHALL expose the loaded rubric identifier, version, and status in every readiness response.
4. THE Rubric_Loader SHALL treat rubric files as read-only at runtime and SHALL require a restart or an explicit reload endpoint for changes to take effect.
5. IF two Role_Rubric files declare the same role, domain, and seniority triple, THEN THE Rubric_Loader SHALL fail to load and SHALL report both file paths.

---

### Requirement 18: Reference role rubrics (RM-RUB-003)

`Milestone: M4 · Priority: P0 · Depends on: RM-RUB-001`

**User Story:** As a maintainer, I want one representative role per domain, so that the architecture is proven to generalize before role coverage expands.

M4 is satisfied by shipping the five reference rubrics with status `draft`. Promoting a rubric to `reviewed` is gated on the validation method resolved by OD-13, not on M4 completion. What M4 proves is that the scoring engine and the configuration architecture generalize across five domains through one code path, and that proof does not depend on rubric status.

#### Acceptance Criteria

1. THE Backend_API SHALL ship five reference Role_Rubric files at M4 completion, one for each of Software Engineering, Finance, Embedded Systems / Hardware, Marketing, and Supply Chain / Operations; these are the architecture-validation set and not a closed product catalogue.
2. THE Software Engineering reference rubric SHALL target Backend Engineer — Intern / New Grad.
3. THE reference rubric for Finance SHALL target Financial Analyst at entry seniority.
4. THE reference rubric for Embedded Systems / Hardware SHALL target Embedded Software / Firmware Engineer at intern-to-entry seniority.
5. THE Marketing reference rubric SHALL target Performance Marketing Analyst — Entry.
6. THE reference rubric for Supply Chain / Operations SHALL target Supply Chain Analyst at entry seniority.
7. THE five reference rubrics SHALL differ only in configuration content and SHALL require no scoring code change relative to one another, verified by a test that scores one fixture profile against all five rubrics through the same code path.
8. `[MAY]` THE Backend_API MAY ship additional schema-conforming Role_Rubric configurations in v1 without changing the scoring engine or introducing a domain-specific scoring branch, provided they use the same deterministic scoring and evidence model and expose their validation status to the Web_Client; they are not required for M4 or the First Closed Loop.
9. `[MAY]` An additional Role_Rubric MAY initially have status `draft`; only a rubric meeting the documented validation requirements for its status, comprising the validation method resolved by OD-13 and the per-rubric weight basis recorded under RM-EXT-002 criterion 5, MAY be labelled `reviewed` or `stable`.
10. THE Backend_API SHALL admit a Role_Rubric whose status is `draft` to readiness scoring and SHALL satisfy the single-code-path proof of criterion 7 irrespective of the status of any rubric, so that the Rubric_Engine and configuration architecture are validated while rubrics remain `draft`; and WHILE a selected Role_Rubric has status `draft`, THE Web_Client SHALL display the unvalidated notice required by RM-EXT-002 criterion 3.

---

### Requirement 19: Deterministic readiness scoring (RM-SCORE-001)

`Milestone: M4 · Priority: P0 · Depends on: RM-RUB-001, RM-EVID-001`

**User Story:** As an early-career professional, I want a readiness score for a role family that I can reproduce and reason about, so that I trust it enough to act on it.

#### Acceptance Criteria

1. WHEN a Candidate_Profile and a Role_Rubric are supplied, THE Rubric_Engine SHALL compute each category's raw score as 100 × (the sum of earned points across that category's declared signals) ÷ (that category's maximum attainable points), where a signal's earned points are its declared signal weight multiplied by the Evidence_Level multiplier for the Evidence_Level assigned to that signal, a signal whose assigned Evidence_Level is below its declared minimum Evidence_Level earns 0 points, the maximum attainable points are the sum of the category's declared signal weights multiplied by the highest multiplier in the mapping, and a category whose maximum attainable points equal 0 receives a raw score of 0 without performing the division.
2. THE Rubric_Engine SHALL derive each reported category score by subtracting the applicable declared penalties from the category's raw score and then clamping the result to the range 0 to 100, so that no penalty drives a reported category score below 0 and no category score exceeds 100.
3. THE Rubric_Engine SHALL compute the overall Readiness_Score from the reported (penalty-adjusted and clamped) category scores as the sum across categories of (reported category score × the category weight declared in the Role_Rubric) ÷ 100, and SHALL clamp the result to the range 0 to 100.
4. THE Rubric_Engine SHALL apply an Evidence_Level multiplier mapping read from configuration that declares exactly one multiplier for each Evidence_Level defined by RM-EVID-001, with every multiplier in the range 0.0 to 1.0, the multiplier for Evidence_Level 0 equal to 0.0, and multipliers non-decreasing as Evidence_Level increases.
5. WHEN a Role_Rubric declares an alternative signal group in which at least one member signal is present at or above the group's declared minimum Evidence_Level, THE Rubric_Engine SHALL credit the group exactly once using the highest Evidence_Level among the qualifying members, SHALL award no separate earned points for the group's remaining members, SHALL count the group once toward the category's maximum attainable points, and SHALL record the identifier of the member signal that produced the credit.
6. IF no member of an alternative signal group is present at or above the group's declared minimum Evidence_Level, THEN THE Rubric_Engine SHALL award the group 0 earned points, SHALL count the group once toward the category's maximum attainable points, and SHALL list the group together with its member signals in the response's missing list.
7. WHEN a Role_Rubric declares a required signal that is absent or present below its declared minimum Evidence_Level, THE Rubric_Engine SHALL subtract the declared penalty points from the score of the category that declares the signal and SHALL list the signal in the response's missing-required list together with the penalty amount applied.
8. THE Rubric_Engine SHALL compute Readiness_Score without invoking an LLM_Provider.
9. THE Rubric_Engine SHALL round each reported category score and the reported Readiness_Score to the nearest integer, rounding halves upward, SHALL apply rounding only to reported values and not to intermediate calculations, and SHALL NOT report fractional precision to the user.
10. IF no declared Role_Rubric signal is matched by the Candidate_Profile at Evidence_Level 1 or higher in any category, THEN THE Rubric_Engine SHALL return a Readiness_Score of 0 with a `no_evidence` reason and a matched-signal count of 0 for every category, rather than an error.
11. IF at least one declared Role_Rubric signal is matched at Evidence_Level 1 or higher and the reported Readiness_Score rounds to 0, THEN THE Rubric_Engine SHALL return a Readiness_Score of 0 with a reason distinct from `no_evidence` indicating that matched evidence scored below the minimum reportable value or was offset by penalties, and SHALL report a matched-signal count greater than 0.
12. THE Rubric_Engine SHALL produce identical per-category scores, applied penalties, and Readiness_Score for repeated computations over identical Candidate_Profile and Role_Rubric inputs within one release version (determinism property).

---

### Requirement 20: Readiness explainability (RM-SCORE-002)

`Milestone: M5 · Priority: P0 · Depends on: RM-SCORE-001`

**User Story:** As a candidate, I want to see which evidence produced each category score and what is missing, so that the number is actionable.

#### Acceptance Criteria

1. THE Rubric_Engine SHALL return, for every category, the category weight, the category score, the matched signals, the missing signals, and the applied penalties.
2. THE Rubric_Engine SHALL return, for every matched signal, its Evidence_Level and the identifiers of the supporting Candidate_Profile items.
3. THE Rubric_Engine SHALL return a factor decomposition whose weighted category contributions sum, within a rounding tolerance of 1 point, to the reported overall Readiness_Score (invariant property).
4. THE Web_Client SHALL display the category breakdown and the missing-required list alongside every Readiness_Score.
5. THE Web_Client SHALL exclude any readiness figure that is not accompanied by its factor decomposition.
6. THE Rubric_Engine SHALL distinguish in its response between signals missing entirely and signals present below the required Evidence_Level.

---

### Requirement 21: Scoring determinism and reproducibility (RM-SCORE-003)

`Milestone: M4 · Priority: P0 · Depends on: RM-SCORE-001`

**User Story:** As a candidate, I want the same resume and role to produce the same score every time, so that I can re-run a result I acted on and dispute it if it changed without my profile changing.

#### Acceptance Criteria

1. FOR ALL pairs of a Candidate_Profile and a Role_Rubric, repeated scoring within one release version SHALL produce identical category scores and an identical Readiness_Score (determinism property).
2. THE Rubric_Engine SHALL exclude wall-clock time, random number generation, network responses, and iteration order of unordered collections from score computation.
3. THE Rubric_Engine SHALL return the rubric version and the engine version alongside every score so that a result can be reproduced.
4. IF a scoring computation raises an exception, THEN THE Backend_API SHALL return HTTP 500 with error code `SCORING_FAILED` and SHALL emit a telemetry event that excludes Candidate_Data.

---

### Requirement 22: Confidence model (RM-CONF-001)

`Milestone: M5 · Priority: P1 · Depends on: RM-PARSE-005, RM-SCORE-001`

**User Story:** As a candidate, I want to know when a result rests on shaky inputs, so that I do not over-trust a score derived from a badly parsed resume.

Confidence in v1 is a deterministic function of measurable inputs, not a model judgement.

For a readiness result, three terms:

`Confidence_Value = w1·mean_extraction_confidence + w2·profile_completeness + w3·signal_coverage`

For a Match_Result, the same three terms plus a fourth:

`Confidence_Value = w1·mean_extraction_confidence + w2·profile_completeness + w3·signal_coverage + w4·job_description_completeness`

where `mean_extraction_confidence` is the mean Extraction_Confidence of the Candidate_Profile items that contributed to the reported score, `profile_completeness` is the fraction of the configured Candidate_Profile sections that are non-empty, `signal_coverage` is the fraction of the loaded Role_Rubric's declared signals whose present-or-absent determination is `determinable` under criterion 8, and `job_description_completeness` is the fraction of the Job_Posting fields mapped to the configuration-enabled match dimensions that are populated. Each of the two term sets carries its own configured weight set.

`signal_coverage` measures whether a determination *could* be made from the parsed profile, not whether the engine rendered one. Under RM-SCORE-001 the Rubric_Engine always renders a verdict, so a term defined as "the fraction of signals for which a verdict was rendered" would be 1.0 for every input and carry no information. A signal the engine determines to be *absent* on the basis of parsed evidence therefore counts as `determinable`: a missing skill lowers Readiness_Score without lowering Confidence_Value.

The `job_description_completeness` denominator is pinned to the dimensions enabled in configuration and evaluated before any dimension exclusion under RM-REQX-003, because counting only the surviving dimensions would make excluding a dimension *raise* the completeness figure — the opposite of what RM-REQX-003 criterion 3 requires.

#### Acceptance Criteria

1. THE Confidence_Calculator SHALL compute Confidence_Value in the closed interval 0.0 to 1.0 for a readiness result from exactly the three terms `mean_extraction_confidence`, `profile_completeness`, and `signal_coverage`, and for a Match_Result from exactly those three terms plus `job_description_completeness`, weighting each term set by its own version-controlled configured weight set, and SHALL reject a weight set at load, without computing any Confidence_Value and with an error naming the offending entries, when the set omits or duplicates a term of its term set, contains a weight below 0.0 or above 1.0, or contains weights that do not sum to 1.0 within a tolerance of 0.001.
2. THE Confidence_Calculator SHALL round Confidence_Value half up to two decimal places before banding and SHALL map the rounded value to `low` below the configured low-medium threshold, proposed as 0.50, to `medium` from the low-medium threshold up to but excluding the configured medium-high threshold, proposed as 0.75, and to `high` from the medium-high threshold to 1.00 inclusive; WHEN the threshold set is loaded, THE Confidence_Calculator SHALL accept it only if both thresholds are present, are values in the range 0.00 to 1.00 inclusive expressed to at most two decimal places, and the low-medium threshold is strictly below the medium-high threshold; IF any of these checks fails, THEN THE Confidence_Calculator SHALL reject the threshold set with an error indicating which constraint was violated and SHALL assign no Confidence_Band until a valid threshold set is supplied.
3. THE Confidence_Calculator SHALL return the value of every input term alongside the Confidence_Band.
4. THE Backend_API SHALL exclude LLM_Provider output from every Confidence_Value input.
5. FOR ALL inputs, repeated confidence computation SHALL produce an identical Confidence_Value (determinism property).
6. THE Web_Client SHALL display the Confidence_Band together with the name and the numeric value of the weakest contributing input, where the weakest contributing input is the term with the lowest term value and, WHEN two or more terms share the lowest term value, the earliest of those terms in the version-controlled configured term order.
7. THE Web_Client SHALL exclude any Confidence_Band display that is not accompanied by its input breakdown.
8. THE Rubric_Engine SHALL record, for every signal declared by the loaded Role_Rubric, whether that signal's present-or-absent determination is `determinable` or `indeterminate`, SHALL record `indeterminate` when and only when one of exactly these three conditions holds — a Candidate_Profile field that the signal requires is absent or failed to parse; the signal's sole supporting Candidate_Profile item carries an Extraction_Confidence below the review threshold of 0.6 defined by RM-PARSE-005 criterion 5 and the user has not confirmed that item under RM-REV-001; a skill-type signal resolves to no Canonical_Skill under RM-SKILL-001 — and SHALL record `determinable` in every other case, including a signal determined to be absent on the basis of parsed evidence.
9. THE Confidence_Calculator SHALL compute each term over exactly the following denominator: `mean_extraction_confidence` over the set of Candidate_Profile items reported as supporting a matched signal under RM-SCORE-002 criterion 2 or as supporting a matched requirement under RM-MATCH-004 criterion 1; `profile_completeness` over the version-controlled configured list of Candidate_Profile sections; `signal_coverage` over the count of signals declared by the loaded Role_Rubric, counting a signal as covered when its determination is `determinable` under criterion 8; and `job_description_completeness` over the Job_Posting fields named by the version-controlled configured dimension-to-field mapping for the match dimensions enabled in configuration, evaluated before any dimension exclusion under RM-REQX-003.
10. IF the denominator of a term under criterion 9 is zero, because no Candidate_Profile item contributed to the reported score, the loaded Role_Rubric declares no signal, or the dimension-to-field mapping names no Job_Posting field, THEN THE Confidence_Calculator SHALL set that term's value to 0.0, SHALL attach a reason code naming the term whose denominator was zero, and SHALL report a Confidence_Band of at most `medium`, excluding `high`.

---

**6 · Job Ingestion**

### Requirement 23: Canonical job posting schema (RM-JOB-001)

`Milestone: M6 · Priority: P0 · Depends on: RM-API-001, RM-SKILL-001`

**User Story:** As an implementing contributor, I want every job source to produce the same record shape, so that matching logic never branches on the source.

#### Acceptance Criteria

1. THE Backend_API SHALL define one Job_Posting schema as a Pydantic model exported as JSON Schema.
2. THE Job_Posting schema SHALL include: internal identifier, source identifier, source external identifier, company, raw title, normalized title, role family, seniority, raw description, location fields, remote or work-mode indicator, employment type, required skills, preferred skills, minimum and maximum experience years, education requirements, certification requirements, apply URL, posted timestamp, and ingestion timestamp.
3. THE Job_Posting schema SHALL mark every field other than internal identifier, source identifier, source external identifier, company, raw title, raw description, and apply URL as optional.
4. FOR ALL valid Job_Posting values, deserializing the serialized form SHALL produce a value equal to the original (round-trip property).
5. THE Job_Normalizer SHALL store the raw description separately from the derived requirement fields.
6. THE Job_Posting schema SHALL exclude every field derived from Candidate_Data.

---

### Requirement 24: Job source adapter interface (RM-JOB-002)

`Milestone: M6 · Priority: P0 (criterion 4: P1) · Depends on: RM-JOB-001`

**User Story:** As an open-source contributor, I want to add a job source by implementing one interface, so that I do not need to understand the matching engine.

The interface, the Fixture adapter, and the source-independence of downstream components are P0. Shipping a live Job_Source_Adapter is a P1 obligation, marked `[P1]` on criterion 4.

#### Acceptance Criteria

1. THE Backend_API SHALL define one Job_Source interface that every Job_Source_Adapter implements.
2. THE Job_Source interface SHALL require a source identifier, a capability declaration, a fetch operation, and a mapping operation returning Job_Posting values.
3. THE Backend_API SHALL ship a Fixture Job_Source_Adapter reading the Fixture_Job_Set from version-controlled files, so that the First Closed Loop can be exercised without network access.
4. `[P1]` THE Backend_API SHALL ship at least one live Job_Source_Adapter for the source resolved by OD-05 as a P1 obligation at M6 completion, and SHALL NOT treat that live adapter as a First Closed Loop obligation; the First Closed Loop is satisfiable with the Fixture Job_Source_Adapter of criterion 3 alone, and criteria 1, 2, 3, 5, 6, and 7 remain P0.
5. THE Matching_Engine SHALL operate on Job_Posting values only and SHALL contain no reference to a specific Job_Source_Adapter.
6. THE Backend_API SHALL isolate every third-party HTTP client behind a Job_Source_Adapter, so that no other component performs job source requests.
7. WHEN a new Job_Source_Adapter is registered, THE Backend_API SHALL require no change to Job_Normalizer, Requirement_Extractor, Matching_Engine, or Classifier code.

---

### Requirement 25: Company and source registry (RM-JOB-003)

`Milestone: M6 · Priority: P1 · Depends on: RM-JOB-002`

**User Story:** As a maintainer, I want a declarative registry of which boards to poll, so that coverage grows by configuration rather than code.

The Source_Registry exists to configure polling of live job boards, so it is a P1 obligation. The First Closed Loop reads the Fixture_Job_Set through the Fixture Job_Source_Adapter and requires no Source_Registry entry.

#### Acceptance Criteria

1. THE Source_Registry SHALL store, per entry, an organization name, a source identifier, a board or account identifier, an enabled flag, and an optional set of role-family filters.
2. THE Backend_API SHALL treat Greenhouse, Lever, and Ashby as per-organization board sources requiring a Source_Registry entry per organization, and SHALL NOT assume a universal search endpoint for them.
3. WHERE a Job_Source_Adapter declares a universal search capability, THE Backend_API SHALL permit query-based ingestion for that adapter without per-organization registry entries.
4. THE Source_Registry SHALL be expressed as a version-controlled configuration file validated against an exported JSON Schema.
5. IF a Source_Registry entry references an unknown source identifier, THEN THE Backend_API SHALL reject the entry at startup and SHALL report the entry.
6. THE Source_Registry SHALL be limited at M6 completion to a documented seed list, and THE Backend_API SHALL treat the obligation that this seed list produce at least 100 Job_Posting records across the five reference role families as a P1 live-ingestion obligation validated by AS-11, rather than as a First Closed Loop gate; the First Closed Loop is validated against the Fixture_Job_Set instead.

---

### Requirement 26: Job source failure handling (RM-JOB-004)

`Milestone: M6 · Priority: P1 (criterion 3: P0) · Depends on: RM-JOB-002`

**User Story:** As a candidate, I want one job board being down to cost me only that board's postings, so that I still get results and know which part of the market I did not see.

Network failure, timeout, and rate-limit handling arise only with live job sources, so criteria 1, 2, 4, 5, and 6 are P1. Criterion 3 concerns per-posting validation failure, which also arises with a malformed fixture posting, so criterion 3 is P0 and is in force on the Fixture path.

#### Acceptance Criteria

1. `[P1]` IF a Job_Source_Adapter request fails, times out, or returns a non-success status, THEN THE Backend_API SHALL record the failure, SHALL continue ingesting from the remaining sources, and SHALL complete the ingestion run.
2. `[P1]` IF a Job_Source_Adapter returns HTTP 429 or a documented rate-limit signal, THEN THE Job_Source_Adapter SHALL apply exponential backoff with a configured maximum retry count and SHALL stop requesting from that source for the remainder of the run once the maximum is reached.
3. `[P0]` IF an individual raw posting fails Job_Posting validation, THEN THE Job_Normalizer SHALL discard that posting, SHALL record a validation-failure event with the source identifier and external identifier, and SHALL continue processing the remaining postings, including when the posting was supplied by the Fixture Job_Source_Adapter.
4. `[P1]` WHEN an ingestion run completes, THE Backend_API SHALL report per source: postings fetched, postings normalized, postings rejected, and failure count.
5. `[P1]` WHEN a job result set is displayed, IF any enabled source failed during the run that produced it, THEN THE Web_Client SHALL display which sources were unavailable.
6. `[P1]` THE Job_Source_Adapter SHALL apply a configured request timeout to every outbound request.

---

### Requirement 27: Duplicate detection (RM-JOB-005)

`Milestone: M6 · Priority: P1 · Depends on: RM-JOB-001`

**User Story:** As a candidate, I want the same job cross-posted to three boards shown to me once, so that my result list reflects how many opportunities exist rather than how many feeds carry them.

#### Acceptance Criteria

1. WHEN two Job_Posting records share a source identifier and a source external identifier, THE Job_Normalizer SHALL treat them as the same posting and SHALL retain the more recently ingested record.
2. WHEN two Job_Posting records from different sources share a normalized company name, a normalized title, and a normalized location, THE Job_Normalizer SHALL mark them as suspected duplicates and SHALL present one of them as primary.
3. THE Web_Client SHALL display suspected duplicates as a single result with the alternative apply URLs available.
4. THE Job_Normalizer SHALL exclude fuzzy description similarity and embedding-based deduplication from v1.

---

### Requirement 28: Coverage disclosure (RM-JOB-006)

`Milestone: M6 · Priority: P1 · Depends on: RM-JOB-003`

**User Story:** As a candidate, I want to know that the job set is partial, so that I do not read "Skip: 78" as a statement about the whole market.

#### Acceptance Criteria

1. THE Web_Client SHALL display, with every job result set, the list of sources queried and the number of organizations covered.
2. THE Web_Client SHALL state that results represent the configured sources only and do not represent the whole job market.
3. THE Web_Client SHALL display the age of the job data used for the result set.
4. THE Web_Client SHALL exclude claims of complete, comprehensive, or global job coverage.

---

### Requirement 29: Separation of public job data from candidate data (RM-JOB-007)

`Milestone: M6 · Priority: P0 (criterion 4: P1) · Depends on: RM-PRIV-001, RM-JOB-001`

**User Story:** As a privacy-conscious candidate, I want my profile kept out of the persistent job cache, so that a database that must be long-lived and widely readable can never hold my resume or my match results.

The Candidate_Data separation obligations of criteria 1, 2, and 3 are P0 and apply to the Fixture path as well as to live sources, because they state a privacy boundary. The persistent-cache maximum-age obligation of criterion 4 applies to live cached postings and is a P1 concern.

#### Acceptance Criteria

1. `[P0]` THE Backend_API SHALL store Public_Job_Data in a persistent store that contains no Candidate_Data.
2. `[P0]` THE Backend_API SHALL exclude candidate identifiers, Session identifiers, and Candidate_Profile content from every Public_Job_Data record and from every job ingestion log record.
3. `[P0]` THE Backend_API SHALL compute Match_Result values in process memory scoped to a Session and SHALL exclude Match_Result values from the Public_Job_Data store.
4. `[P1]` THE Backend_API SHALL apply a configured maximum age to Job_Posting records held in the persistent Public_Job_Data cache from a live Job_Source_Adapter and SHALL exclude postings older than that age from result sets; THE Backend_API SHALL NOT apply that maximum age to Job_Posting records supplied by the Fixture Job_Source_Adapter, so that the First Closed Loop does not depend on fixture posting timestamps.

---

### Requirement 30: Prohibited job sources in v1 (RM-JOB-008)

`Milestone: M6 · Priority: P0 · Depends on: RM-JOB-002`

**User Story:** As a maintainer, I want the permitted source list and each endpoint's documentation recorded in the repository, so that a contributor's convenient scraper does not expose the project to a takedown notice or a terms-of-service claim.

#### Acceptance Criteria

1. THE Backend_API SHALL restrict v1 job sources to public ATS endpoints and documented job APIs, specifically Greenhouse, Lever, Ashby, Adzuna, and USAJobs, plus the Fixture adapter.
2. THE Backend_API SHALL exclude LinkedIn and Indeed scraping from v1.
3. THE Backend_API SHALL exclude HTML scraping of any site whose terms prohibit automated access from v1.
4. THE Backend_API SHALL record, per Job_Source_Adapter, the documentation URL for the endpoint it consumes.

---

**7 · Job Requirement Extraction**

### Requirement 31: Required versus preferred requirements (RM-REQX-001)

`Milestone: M7 · Priority: P0 · Depends on: RM-JOB-001, RM-SKILL-001`

**User Story:** As a candidate, I want the system to know the difference between a must-have and a nice-to-have, so that I am not told to skip a job over a preference.

#### Acceptance Criteria

1. WHEN a Job_Posting description is processed, THE Requirement_Extractor SHALL assign to every extracted requirement exactly one classification from `required`, `preferred`, or `contextual`, and SHALL support descriptions of at least 50,000 characters yielding at least 200 requirement units per posting.
2. THE Requirement_Extractor SHALL classify a requirement unit as `required` when the unit's own text matches an entry in the configured required-language pattern set, or when the unit lies within the scope of a heading whose text matches that set, where a heading's scope runs from the heading line to the next heading of the same or higher level or to the end of the description, and where pattern matching is case-insensitive at whole-word boundaries.
3. THE Requirement_Extractor SHALL classify a requirement unit as `preferred` when the unit's own text matches an entry in the configured preferred-language pattern set, or when the unit lies within the scope of a heading whose text matches that set, using the same heading-scope and matching rules as criterion 2.
4. THE Requirement_Extractor SHALL classify a requirement unit as `contextual` when the unit matches the configured contextual-language pattern set covering teamwork, culture, and company-values language and the unit yields no Canonical_Skill after normalization, and SHALL exclude every `contextual` requirement from match scoring and from Hard_Requirement evaluation.
5. IF a requirement unit matches neither the required nor the preferred pattern set, or if criterion 10 leaves its classification unresolved, THEN THE Requirement_Extractor SHALL classify the unit as `preferred`, SHALL flag the classification as low-confidence, and SHALL NOT assign `required` to any unmatched or unresolved unit.
6. THE Requirement_Extractor SHALL normalize every extracted skill requirement through the Skill_Normalizer before recording its classification, and SHALL exclude a requirement whose Canonical_Skill resolves to `unmapped` under RM-SKILL-001 criterion 3 from Hard_Requirement evaluation while retaining it in the extracted requirement set for display.
7. THE Requirement_Extractor SHALL record, for each extracted requirement, the zero-based start offset and the exclusive end offset of the source phrase within the raw description, such that extracting that span from the raw description reproduces the source phrase exactly.
8. THE Requirement_Extractor SHALL operate deterministically without an LLM_Provider for the First Closed Loop, SHALL produce identical classifications for identical Job_Posting description input within one release version, SHALL record with every extracted requirement the version identifiers of the pattern sets and the delimitation rule set applied, and SHALL treat LLM-assisted extraction as a configurable, separately evaluated path resolved by OD-06.
9. WHEN a Job_Posting description is processed, THE Requirement_Extractor SHALL delimit requirement units before classification by treating each list item as one unit and each sentence of non-list prose as one unit, SHALL split any unit longer than 400 characters at the nearest clause boundary and flag each unit produced by such a split as low-confidence, and SHALL derive at most one requirement per distinct Canonical_Skill per unit (delimitation rule set recorded as a v1 assumption under AS-05).
10. IF more than one classification signal applies to one requirement unit, THEN THE Requirement_Extractor SHALL resolve the classification in this fixed order — `contextual` when a contextual signal is present and the unit yields no Canonical_Skill, then `preferred` when any preferred signal is present at unit or heading scope, then `required` when a required signal is present at unit or heading scope — so that a unit carrying both required and preferred signals is classified `preferred`.
11. THE Requirement_Extractor SHALL achieve at least 0.90 precision on the `required` class and at least 0.80 agreement across all three classes, measured against the hand-labeled sample of at least 100 Job_Posting records required by AS-05, and RM-TEST-001 SHALL fail the build when either figure regresses below these thresholds.

---

### Requirement 32: Experience, seniority, and education extraction (RM-REQX-002)

`Milestone: M7 · Priority: P0 · Depends on: RM-REQX-001`

**User Story:** As a new graduate, I want "3+ years" and a stated degree read as the posting wrote them, so that an entry-level role is not judged against a senior bar and a senior role is not recommended to me.

#### Acceptance Criteria

1. WHEN a description states a years-of-experience range, THE Requirement_Extractor SHALL populate the minimum and maximum experience years fields.
2. WHEN a description states a single minimum such as "3+ years", THE Requirement_Extractor SHALL populate the minimum field and SHALL leave the maximum field unpopulated.
3. THE Requirement_Extractor SHALL derive seniority from a configured mapping over title tokens and stated experience, using one of `intern`, `entry`, `mid`, `senior`, `lead`, or `unknown`.
4. WHEN a description states a minimum degree level or field, THE Requirement_Extractor SHALL populate the education requirement fields and SHALL record whether the requirement is `required` or `preferred`.
5. IF conflicting experience figures appear in one description, THEN THE Requirement_Extractor SHALL retain the lowest stated minimum and SHALL flag the field as conflicting.
6. IF seniority cannot be derived, THEN THE Requirement_Extractor SHALL set seniority to `unknown` and the Matching_Engine SHALL exclude the seniority dimension for that posting.

---

### Requirement 33: Tolerance for incomplete job descriptions (RM-REQX-003)

`Milestone: M7 · Priority: P0 (criterion 3: P1) · Depends on: RM-REQX-001, RM-CONF-001`

**User Story:** As a candidate, I want a vaguely written posting marked as unclear rather than scored as a poor fit, so that I am not told to skip a job the system simply could not read.

Criterion 3 depends on RM-CONF-001 and is therefore a P1 obligation. Criteria 1, 2, 4, and 5 — dimension exclusion, weight redistribution, the `insufficient_job_data` classification, and no-exception tolerance — remain P0, since deterministic matching against fixture postings needs them.

#### Acceptance Criteria

1. IF a Job_Posting description yields no extractable skill requirement, THEN THE Requirement_Extractor SHALL return an empty requirement set and the Matching_Engine SHALL exclude the skills dimension for that posting.
2. WHEN a match dimension is excluded for a posting, THE Matching_Engine SHALL redistribute that dimension's weight proportionally across the remaining enabled dimensions and SHALL record which dimensions were excluded.
3. WHEN two or more match dimensions are excluded for a posting, THE Confidence_Calculator SHALL reduce `job_description_completeness` accordingly and the Web_Client SHALL display the resulting Confidence_Band.
4. IF fewer than two match dimensions can be evaluated for a posting, THEN THE Classifier SHALL assign `stretch` with reason code `insufficient_job_data` rather than `skip`.
5. THE Requirement_Extractor SHALL complete without raising an exception for every malformed-description fixture in RM-TEST-002.

---

**8 · Matching and Classification**

### Requirement 34: Deterministic match scoring (RM-MATCH-001)

`Milestone: M8 · Priority: P0 · Depends on: RM-REQX-001, RM-SCORE-001`

**User Story:** As a candidate, I want a per-job fit score that accounts for seniority and constraints rather than keyword overlap, so that the ranking reflects whether I would realistically be considered.

The v1 dimension weights below are **unvalidated assumptions** carried from the handoff. They are recorded as AS-07 with the validation method in that assumption. They must be configuration, not constants in code.

| Dimension | Proposed v1 weight |
|---|---:|
| Skills | 30% |
| Experience | 20% |
| Role similarity | 15% |
| Seniority | 10% |
| Education | 10% |
| Location / work mode | 10% |
| Domain signals | 5% |

#### Acceptance Criteria

1. WHEN a Candidate_Profile and a Job_Posting are supplied, THE Matching_Engine SHALL compute a per-dimension score in the inclusive range 0 to 100 for each enabled dimension and, where at least one dimension is enabled, an overall match score in the inclusive range 0 to 100, clamping to the nearer bound any value that applied penalties would drive outside that range.
2. THE Matching_Engine SHALL read from version-controlled configuration exactly one weight for each of the seven dimensions named in the table above, and SHALL reject at load, without computing any match score and with an error indicating the offending entries, a weight set whose weights do not sum to 100 within a tolerance of 0.01, or that contains a weight below 0 or above 100, or that omits or duplicates a dimension.
3. THE Matching_Engine SHALL weight each matched skill by its Evidence_Level using a configured mapping that declares exactly one multiplier for every Evidence_Level defined in RM-EVID-001 and is non-decreasing as Evidence_Level increases, and SHALL reject a mapping that omits an Evidence_Level or violates that ordering.
4. THE Matching_Engine SHALL read the absent-Preferred_Requirement penalty and the absent-Hard_Requirement penalty from configuration and SHALL reject a penalty set in which the absent-Preferred_Requirement penalty is not strictly smaller than the absent-Hard_Requirement penalty, verified by a test asserting the ordering of the two penalties.
5. THE Matching_Engine SHALL compute every per-dimension score and the overall match score without invoking an LLM_Provider.
6. THE Matching_Engine SHALL round every reported per-dimension score and the reported overall match score to the nearest integer, resolving a value exactly halfway between two integers to the larger integer, and SHALL apply rounding to reported values only and not to intermediate weighted contributions.
7. THE Matching_Engine SHALL compute every dimension score from the extracted and normalized requirement set and the structured Job_Posting fields only, excluding the raw description text, verified by a test asserting that two Job_Posting records differing only in raw description wording, but yielding identical extracted requirements and identical structured fields, produce identical per-dimension scores and an identical overall match score.
8. THE Matching_Engine SHALL record in the Match_Result the enabled dimensions, the excluded dimensions each with its exclusion reason, the effective weights after any redistribution under RM-REQX-003 which SHALL sum to 100 within a tolerance of 0.1 whenever at least one dimension is enabled, the per-dimension scores, and an absent overall match score when no dimension is enabled.
9. THE Matching_Engine SHALL treat a dimension as enabled for a posting only when the inputs that dimension consumes are present — skills: a non-empty extracted requirement set; experience: a populated Job_Posting minimum experience years value and a derivable Candidate_Profile total relevant experience; seniority: a Job_Posting seniority other than `unknown`; education: a populated Job_Posting education requirement; location / work mode: both a user-set location or work-mode constraint and a populated Job_Posting location or work-mode indicator; role similarity: a populated Job_Posting role family or normalized title; domain signals: a posting domain derivable under criterion 11 — and SHALL exclude every dimension whose consumed inputs are absent, applying the weight redistribution and recording obligations of RM-REQX-003.
10. THE Matching_Engine SHALL compute the role similarity dimension score by comparing the Job_Posting role family and normalized title against the Candidate_Profile target role and prior role titles using a version-controlled configured role-family equivalence table that declares one score in the range 0 to 100 for each ordered pair of role families, and SHALL score a pair absent from that table as 0.
11. THE Matching_Engine SHALL derive the posting domain from a version-controlled configured mapping over the Job_Posting company and role family, SHALL compute the domain signals dimension score by comparing that posting domain against the Candidate_Profile target domain and the domains mapped from its prior employers, and SHALL score a domain pair absent from that mapping as 0.

---

### Requirement 35: Hard requirement handling (RM-MATCH-002)

`Milestone: M8 · Priority: P0 · Depends on: RM-MATCH-001`

**User Story:** As a candidate, I want a job ruled out only when I genuinely cannot be considered for it, so that the tool does not quietly hide opportunities I could have won.

The disqualification thresholds below are **unvalidated assumptions** on the same footing as AS-08 and must be configuration, not constants in code. A false `skip` costs the user a real opportunity, so every condition below is stated as a data-availability-guarded test.

#### Acceptance Criteria

1. THE Matching_Engine SHALL treat a requirement classified as `required` by the Requirement_Extractor as a Hard_Requirement, and SHALL exclude from Hard_Requirement treatment every requirement classified as `preferred` or `contextual` and every requirement falling in the excluded categories of criterion 6.
2. WHEN a Hard_Requirement is unmet, THE Matching_Engine SHALL apply the configured hard-requirement penalty exactly once for that requirement, SHALL list the requirement in the Match_Result's unmet-required list, and SHALL confine the penalty's effect to the overall match score.
3. WHEN the count of unmet Hard_Requirements meets or exceeds the configured unmet-required threshold, expressed as an integer in the range 1 to 10 and proposed as 2, THE Classifier SHALL assign `skip` with reason code `hard_requirement_failure` irrespective of the overall match score.
4. WHERE the Job_Posting's minimum experience years field is populated and is not flagged as conflicting under RM-REQX-002, WHEN the stated minimum exceeds `Total_Relevant_Experience` by more than the configured seniority tolerance, expressed as an integer number of years in the range 0 to 10 and proposed as 2, THE Classifier SHALL assign `skip` with reason code `seniority_mismatch`.
5. WHERE the user has set a location or work-mode constraint in the Candidate_Profile, WHEN either the Job_Posting's work-mode indicator is populated and conflicts with the user's work-mode constraint, or the Job_Posting's work-mode indicator states a non-remote arrangement and its populated normalized location matches no entry in the user's declared location set, THE Classifier SHALL assign `skip` with reason code `location_incompatible`.
6. THE Matching_Engine SHALL exclude work authorization, visa status, and sponsorship requirements from v1 Hard_Requirement evaluation, SHALL exclude them from the unmet-required count of criterion 3 and from every score penalty, and SHALL surface the source requirement text to the user as an informational note that does not alter the match score or the Match_Class.
7. THE Matching_Engine SHALL list every unmet Hard_Requirement with its normalized requirement identifier, the source phrase character offsets recorded under RM-REQX-001, and the distinction between absent evidence and evidence below the required Evidence_Level.
8. THE Matching_Engine SHALL compute `Total_Relevant_Experience` as the total duration of the Candidate_Profile experience entries admitted by the configured relevance rule, counting any calendar period covered by two or more entries once, expressed in years to one decimal place and truncated toward zero / rounded down, and SHALL record the computed value together with the identifiers of the contributing entries in the Match_Result; for example, 17 months is 1.4 years and 18 months is 1.5 years.
9. IF a disqualifying condition under criterion 4 or criterion 5 cannot be evaluated because the Job_Posting minimum experience years field, location fields, and work-mode indicator are unpopulated, or because no dated Candidate_Profile experience entry is available to compute `Total_Relevant_Experience`, THEN THE Classifier SHALL NOT assign `skip` on that condition, SHALL exclude the corresponding match dimension per RM-REQX-003, and SHALL record reason code `insufficient_job_data`.
10. WHEN one or more disqualifying conditions under criteria 3, 4, or 5 apply, THE Classifier SHALL assign `skip`, SHALL attach the reason code of every applicable condition, and SHALL record that the assignment came from a disqualifying condition rather than from the score thresholds of RM-MATCH-003.

---

### Requirement 36: Classification into three bands (RM-MATCH-003)

`Milestone: M8 · Priority: P0 · Depends on: RM-MATCH-001, RM-MATCH-002`

**User Story:** As a candidate facing hundreds of postings, I want them sorted into apply, stretch, and skip, so that I can decide where to spend my effort.

The thresholds below are **unvalidated assumptions** recorded as AS-08.

#### Acceptance Criteria

1. WHEN a Match_Result is produced, THE Classifier SHALL assign to it exactly one Match_Class from the closed set `strong_apply`, `stretch`, `skip`, such that no Match_Result is left unclassified and no Match_Result carries more than one Match_Class.
2. THE Classifier SHALL evaluate assignment rules in the fixed precedence order (1) a disqualifying condition of RM-MATCH-002, (2) the insufficient-data override of RM-REQX-003, (3) presence of an unmet Hard_Requirement below the RM-MATCH-002 skip threshold, (4) the score thresholds — and SHALL apply the first rule whose conditions hold, ignoring every lower-precedence rule.
3. IF a disqualifying condition of RM-MATCH-002 applies to a posting, THEN THE Classifier SHALL assign `skip` irrespective of the overall match score, including a score at or above the strong-apply threshold.
4. IF no disqualifying condition of RM-MATCH-002 applies, no Hard_Requirement is unmet, and the overall match score is at or above the configured strong-apply threshold, proposed as 75, THEN THE Classifier SHALL assign `strong_apply`.
5. IF no disqualifying condition of RM-MATCH-002 applies, the overall match score is at or above the configured stretch threshold, proposed as 55, and either the score is below the strong-apply threshold or at least one Hard_Requirement is unmet, THEN THE Classifier SHALL assign `stretch`.
6. IF no disqualifying condition of RM-MATCH-002 applies, the overall match score is below the configured stretch threshold, and the insufficient-data override of RM-REQX-003 does not apply, THEN THE Classifier SHALL assign `skip`.
7. WHEN the overall match score equals a configured threshold exactly, THE Classifier SHALL assign the higher of the two bands bounded by that threshold, verified by tests at threshold minus 1, threshold, and threshold plus 1 for both thresholds.
8. WHEN the threshold configuration is loaded, THE Classifier SHALL accept the threshold set only if both thresholds are present, are integers in the range 0 to 100 inclusive, and the stretch threshold is strictly below the strong-apply threshold; IF any of these checks fails, THEN THE Classifier SHALL reject the threshold set with an error indicating which constraint was violated and SHALL assign no Match_Class until a valid threshold set is supplied.
9. WHEN the Classifier assigns `skip` or `stretch`, THE Classifier SHALL attach at least one and at most five reason codes in a deterministic order that is identical across repeated runs of the same inputs.
10. THE Classifier SHALL draw every attached reason code from the closed enumeration `hard_requirement_failure`, `seniority_mismatch`, `location_incompatible`, `insufficient_job_data`, `unmet_hard_requirement`, `score_below_strong_apply_threshold`, `score_below_stretch_threshold`, and SHALL attach no code outside that enumeration.
11. THE Classifier SHALL emit no Match_Class value other than the three named in criterion 1 and SHALL expose no configuration option that enables a fourth `apply` band in v1, per conflict resolution C-1, with the four-band variant deferred as OD-08b.
12. WHEN a result set has been analyzed, THE Web_Client SHALL display a count for each of the three Match_Class values, SHALL display zero for a class containing no postings, and the three displayed counts SHALL sum to the number of Match_Results in that result set.

---

### Requirement 37: Match explanation (RM-MATCH-004)

`Milestone: M8 · Priority: P0 · Depends on: RM-MATCH-001`

**User Story:** As a candidate, I want to see why a job was classified the way it was, so that I can act on it or disagree with it.

#### Acceptance Criteria

1. THE Matching_Engine SHALL return, per Match_Result, the per-dimension scores, the matched requirements with their supporting Candidate_Profile item identifiers, the unmet required requirements, and the unmet preferred requirements.
2. THE Matching_Engine SHALL return a factor decomposition whose weighted dimension contributions sum, within a rounding tolerance of 1 point, to the reported overall match score (invariant property).
3. THE Web_Client SHALL display the match score together with its dimension breakdown and its unmet-requirement lists.
4. THE Web_Client SHALL exclude any match score that is not accompanied by its factor decomposition.
5. THE Matching_Engine SHALL distinguish, per requirement, between absent evidence and evidence present below the required Evidence_Level.
6. THE Matching_Engine SHALL produce explanations from deterministic data and SHALL NOT depend on an LLM_Provider being configured.

---

### Requirement 38: Matching determinism (RM-MATCH-005)

`Milestone: M8 · Priority: P0 · Depends on: RM-MATCH-001`

**User Story:** As a maintainer, I want an identical profile and posting to yield an identical Match_Result regardless of result-set ordering, so that a change in weights or extraction shows up as a diff against the fixture baselines instead of hiding in run-to-run noise.

#### Acceptance Criteria

1. FOR ALL pairs of a Candidate_Profile and a Job_Posting, repeated matching within one release version SHALL produce an identical Match_Result and an identical Match_Class (determinism property).
2. THE Matching_Engine SHALL produce results independent of the order in which Job_Posting records are supplied (confluence property).
3. THE Matching_Engine SHALL exclude wall-clock time, random number generation, and network responses from score computation.
4. THE Matching_Engine SHALL return the weight-set version and the engine version alongside every Match_Result.
5. IF matching raises an exception for one Job_Posting, THEN THE Backend_API SHALL exclude that posting from the result set, SHALL record the failure, and SHALL return the remaining results.

---

**9 · LLM Layer**

### Requirement 39: Provider interface (RM-LLM-001)

`Milestone: M10 · Priority: P1 · Depends on: RM-PRIV-003`

**User Story:** As a maintainer, I want model providers behind one interface, so that adding a local or alternative provider does not touch product logic.

#### Acceptance Criteria

1. THE Backend_API SHALL define one LLM_Provider interface with named operations for explaining a readiness result, explaining a match result, generating application guidance, summarizing skill gaps, and performing bounded extraction.
2. THE Backend_API SHALL route every LLM_Provider call through the LLM_Gateway.
3. THE Backend_API SHALL ship exactly one cloud LLM_Provider implementation at M10 completion.
4. THE Backend_API SHALL declare, per LLM_Provider, whether it executes locally or across the Cloud_Boundary.
5. THE Backend_API SHALL select the active LLM_Provider from configuration without a code change.
6. WHERE no LLM_Provider is configured, THE Backend_API SHALL serve the complete deterministic workflow through classification, and SHALL return a documented `guidance_unavailable` state for LLM-dependent outputs.
7. THE Backend_API SHALL exclude additional cloud providers from v1 scope.

---

### Requirement 40: LLMs never own numeric scoring (RM-LLM-002)

`Milestone: M10 · Priority: P0 · Depends on: RM-SCORE-001, RM-MATCH-001`

**User Story:** As a candidate, I want every number I act on computed by rules I can read, so that the decision to skip a job is not a model's guess that changes when the model changes.

#### Acceptance Criteria

1. THE Backend_API SHALL compute Readiness_Score, category scores, match scores, dimension scores, Evidence_Level, Confidence_Value, and Match_Class in deterministic components only.
2. THE Backend_API SHALL exclude LLM_Provider output from every field named in criterion 1.
3. IF an LLM_Provider response contains a numeric value in a field reserved for deterministic scoring, THEN THE LLM_Gateway SHALL discard the value and SHALL emit a telemetry event of severity `warning`.
4. RM-TEST-001 SHALL include a test that runs the full readiness and matching pipeline with the LLM_Provider replaced by a stub returning arbitrary numbers, and asserts that all scores and classes are unchanged.
5. THE LLM_Gateway SHALL restrict LLM_Provider responsibilities to natural-language explanation, summarization, coaching text, and bounded extraction of named fields.

---

### Requirement 41: Structured output validation and failure handling (RM-LLM-003)

`Milestone: M10 · Priority: P1 · Depends on: RM-LLM-001`

**User Story:** As a candidate, I want a model outage or a malformed model reply to cost me only the written guidance, so that my readiness score and job results still arrive instead of the page failing.

#### Acceptance Criteria

1. THE LLM_Gateway SHALL define a response schema for every LLM_Provider operation and SHALL validate every response against its schema.
2. IF an LLM_Provider response fails schema validation, THEN THE LLM_Gateway SHALL retry once and, on a second failure, SHALL return a `guidance_unavailable` state to the caller.
3. IF an LLM_Provider request exceeds the configured timeout, THEN THE LLM_Gateway SHALL abandon the request and SHALL return a `guidance_unavailable` state.
4. IF an LLM_Provider is unreachable, THEN THE Backend_API SHALL return the deterministic results and SHALL return a `guidance_unavailable` state for LLM-dependent fields.
5. WHEN a `guidance_unavailable` state is returned, THE Web_Client SHALL display the deterministic results and SHALL state that written guidance is temporarily unavailable.
6. THE LLM_Gateway SHALL apply a configured maximum token or character budget to every request; WHEN a request would exceed that budget, THE LLM_Gateway SHALL reduce the request by omitting entire eligible field paths or entire evidence items, in a documented deterministic priority order read from version-controlled configuration, until the request fits the budget; THE LLM_Gateway SHALL NOT truncate, concatenate, summarize, paraphrase, or otherwise alter the value at any included candidate-derived field path in order to satisfy the budget, so that the value at every included candidate-derived field path remains equal to the value at the same field path of the Session's current Sanitized_Resume and the reduced request remains a valid projection under RM-PRIV-003 criterion 2; THE LLM_Gateway SHALL treat as ineligible for omission every field path that the response schema of the requested operation under criterion 1 requires, and SHALL treat every other candidate-derived field path and every evidence item as eligible; THE LLM_Gateway SHALL produce an identical reduced request for identical inputs and an identical budget (determinism property); THE LLM_Gateway SHALL record, in the Session's Cloud_LLM_Request manifest entry under RM-PRIV-003 criterion 8, which field paths and which evidence items were omitted for budget reasons, and SHALL make that record available to the Privacy_Inspector under RM-PRIV-004; and IF the request cannot be brought within the budget after every eligible field path and every eligible evidence item has been omitted, THEN THE LLM_Gateway SHALL return a `guidance_unavailable` state and SHALL transmit no altered candidate-derived value.
7. THE LLM_Gateway SHALL exclude exact-string equality from response validation, asserting schema conformance and grounding instead.

---

### Requirement 42: Evidence grounding (RM-LLM-004)

`Milestone: M10 · Priority: P0 · Depends on: RM-LLM-003, RM-EVID-001`

**User Story:** As a candidate, I want every sentence written about me traceable to a line in my own resume, so that guidance never invents a skill or a job I would then have to defend in an interview.

#### Acceptance Criteria

1. THE LLM_Gateway SHALL include in every explanation or guidance request the set of Canonical_Skill identifiers and Candidate_Evidence item identifiers the model is permitted to reference.
2. THE LLM_Gateway SHALL require that every skill or experience claim in a model response cite a permitted Candidate_Evidence item identifier.
3. IF a model response references a skill or experience absent from the permitted set, THEN THE LLM_Gateway SHALL remove the offending statement, SHALL emit a telemetry event of severity `warning` naming the ungrounded item, and SHALL return the remaining validated content.
4. IF more than a configured fraction of statements in one response are ungrounded, THEN THE LLM_Gateway SHALL discard the entire response and SHALL return a `guidance_unavailable` state.
5. WHEN a requested fact is absent from the permitted evidence set, THE LLM_Gateway SHALL require the model to return an explicit `unknown` value rather than an inferred one, enforced by schema validation.

---

**10 · Application Guidance**

### Requirement 43: Per-job application guidance (RM-COACH-001)

`Milestone: M10 · Priority: P1 · Depends on: RM-MATCH-004, RM-LLM-004`

**User Story:** As a career switcher, I want to know how to present my real background for a specific job, so that I can apply effectively without misrepresenting myself.

#### Acceptance Criteria

1. WHEN a user opens a Job_Posting classified `strong_apply` or `stretch`, THE Application_Coach SHALL return the strongest matched evidence, the unmet required requirements, the unmet preferred requirements, and the requirements met below the required Evidence_Level.
2. THE Application_Coach SHALL return, for each recommendation, the Candidate_Evidence item identifiers or Job_Posting requirement offsets on which it is based.
3. THE Application_Coach SHALL restrict resume recommendations to: reordering existing content, emphasizing existing content, quantifying existing content where a figure is already present in the source text, and rewording existing content.
4. THE Application_Coach SHALL return a `do_not_claim` list naming the job's requirements for which the candidate has no supporting evidence.
5. THE Application_Coach SHALL derive the recommendation about whether to apply from the Match_Class and SHALL NOT let an LLM_Provider override it.
6. `[SHOULD]` THE Application_Coach SHOULD identify Candidate_Profile items that are unrelated to the Job_Posting's requirements so the user can deprioritize them.
7. THE Application_Coach SHALL exclude cover letter generation, full resume rewriting, and automated application submission from v1.

---

### Requirement 44: No fabricated experience (RM-COACH-002)

`Milestone: M10 · Priority: P0 · Depends on: RM-COACH-001, RM-LLM-004`

**User Story:** As a candidate, I want the tool to never suggest that I claim something untrue, so that following its advice does not put my credibility at risk.

#### Acceptance Criteria

1. THE Application_Coach SHALL derive, for each guidance response, a permitted-claim set consisting of (a) the Canonical_Skill identifiers produced by the Skill_Normalizer from the source text of the Candidate_Profile items cited under RM-COACH-001 criterion 2, (b) the employer names, role titles, and certification names appearing verbatim in those items, and (c) the numeric tokens appearing in those items, and SHALL exclude from the response any resume-content recommendation that names a skill, employment record, project, certification, achievement, or numeric figure whose normalized form is absent from that set. Paraphrase is decided by Skill_Normalizer equivalence, not by string equality: a surface string that normalizes to a permitted Canonical_Skill is permitted, and a surface string that normalizes to a Canonical_Skill outside the set, or that names an organization or credential outside the set, is a fabrication.
2. WHEN a Job_Posting requirement names a Canonical_Skill assigned Evidence_Level 0 under RM-EVID-001, THE Application_Coach SHALL place exactly one `do_not_claim` entry for that Canonical_Skill in the same response, and SHALL restrict every mention of that skill in that response to a learning recommendation or a future-project recommendation stated in forward-looking terms.
3. THE Application_Coach SHALL exclude from every resume-content recommendation any numeric token — digit sequence, spelled-out cardinal, percentage, currency amount, or duration — that does not match a numeric token in the source text of at least one cited Candidate_Profile item, where matching is exact numeric-value equality after normalizing thousands separators, decimal notation, spelled-out forms to digits, and percent or currency notation to a value plus unit. Numeric tokens appearing only in the Job_Posting SHALL NOT satisfy this check.
4. THE Application_Coach SHALL restrict resume-content recommendations to the four recommendation types enumerated in RM-COACH-001 criterion 3, SHALL label each recommendation with exactly one of those types, and SHALL exclude any recommendation that both cites an existing item and introduces a Canonical_Skill, organization, credential, or numeric token absent from that item's source text — this being the decision boundary between rewording existing content and fabrication.
5. THE Application_Coach SHALL exclude any recommendation that describes a Canonical_Skill at a strength above its assigned Evidence_Level, and SHALL exclude proficiency qualifiers such as "expert", "advanced", or "extensive" that do not appear in the source text of a cited Candidate_Profile item.
6. IF a model response contains a statement that fails the check in criterion 1, 3, 4, or 5, THEN THE LLM_Gateway SHALL treat the statement as a fabrication attempt, SHALL remove it under RM-LLM-004 criterion 3, SHALL return the remaining validated content, and SHALL record a fabrication-attempt event naming the violated check and the offending item identifier, excluding candidate-derived text per RM-OBS-002.
7. THE Backend_API SHALL apply the checks in criteria 1, 3, 4, and 5 as a deterministic validator over every Application_Coach response before the response leaves the Backend_API, independently of prompt content, and IF the validator cannot complete, THEN THE Backend_API SHALL return a `guidance_unavailable` state rather than the unvalidated response.
8. RM-TEST-001 SHALL include a fabrication-pressure test suite that pairs the candidate profile fixtures of RM-TEST-002 criterion 5 with Job_Posting fixtures each demanding at least three Canonical_Skills at Evidence_Level 0, covering at least 20 profile-posting pairings across all five reference roles, and SHALL assert for every pairing that: no recommendation names a claim outside the permitted-claim set of criterion 1; no recommendation contains a numeric token failing criterion 3; every requirement skill at Evidence_Level 0 appears exactly once in the `do_not_claim` list; and every mention of such a skill occurs only in a learning or future-project recommendation.
9. THE fabrication-pressure test suite SHALL include at least 10 deterministic LLM_Provider stub responses that bypass prompt wording, covering at least these fabrication forms: adding an absent skill, inflating a years-of-experience figure, inventing an employer, inventing a certification, inventing a quantified achievement, upgrading a Declared skill to production experience, an implied claim expressed as paraphrase, and an explicit imperative to state an unevidenced claim; SHALL assert that each offending statement is absent from the returned response; SHALL assert that one fabrication-attempt event is recorded per injected violation; and SHALL fail the build on any failure without an override path per RM-TEST-001 criterion 8.
10. THE Backend_API SHALL compute the fabrication-attempt event rate as fabrication-attempt events divided by guidance responses over a rolling 7-day window, SHALL publish it as a tracked quality metric with a target of zero, and IF the rate exceeds zero in a window, THEN THE Backend_API SHALL emit a telemetry event of severity `warning`.

---

### Requirement 45: Opportunity gain (deferred) (RM-OPP-001)

`Milestone: M12 · Priority: P2 · Depends on: RM-MATCH-003`

**User Story:** As an early-career professional, I want to know which missing skill would unlock the most opportunities, so that I learn the highest-value thing next.

**Cost note.** As specified in the source documents, Opportunity_Gain requires re-running the match pipeline over the full result set under one counterfactual Candidate_Profile per candidate skill. For *n* postings and *k* candidate skills this is *n·k* match evaluations per refresh, and the resulting estimate has no ground truth to validate against without candidate outcome data the product does not collect. This requirement is therefore excluded from the First Closed Loop and from v1, and its validation method is an open question (OD-19).

#### Acceptance Criteria

1. THE Opportunity_Analyzer SHALL compute, per missing Canonical_Skill, the frequency with which the skill appears as a required or preferred requirement across the analyzed result set.
2. THE Opportunity_Analyzer SHALL express frequency as a count and a percentage of the analyzed postings and SHALL name the role families in which the skill appears.
3. `[SHOULD]` THE Opportunity_Analyzer SHOULD compute Opportunity_Gain as the number of postings whose Match_Class improves when the missing skill is credited at a stated Evidence_Level.
4. WHERE Opportunity_Gain is computed, THE Opportunity_Analyzer SHALL state the assumed Evidence_Level and SHALL label the figure as an estimate.
5. THE Opportunity_Analyzer SHALL derive all figures from deterministic components and SHALL exclude LLM_Provider output.
6. THE Backend_API SHALL apply a configured evaluation budget to Opportunity_Gain computation and SHALL return partial results with a truncation marker when the budget is exhausted.
7. THE Web_Client SHALL exclude any claim that acquiring a skill will produce an interview or an offer.

---

**11 · User Interface and Journey**

### Requirement 46: Candidate readiness screens (RM-UI-001)

`Milestone: M5 · Priority: P0 (criterion 4 Confidence_Band display: P1) · Depends on: RM-SCORE-002, RM-CONF-001`

**User Story:** As an early-career professional, I want a usable readiness result for my chosen role before any job board is connected, so that I get something I can act on without waiting for job ingestion to be configured.

The readiness screen is P0 without the Confidence_Band element of criterion 4; the overall Readiness_Score, the per-category scores, the strengths list, and the gaps list are P0. The Confidence_Band element arrives with RM-CONF-001 at P1.

#### Acceptance Criteria

1. THE Web_Client SHALL provide screens for upload, parsed profile review, career target selection, and candidate readiness.
2. THE Web_Client SHALL require the user to select a domain and a role before requesting a readiness score.
3. THE Web_Client SHALL allow the user to set experience level, location, and work mode as target constraints.
4. THE Web_Client SHALL display the overall Readiness_Score, the per-category scores, the strengths list, the gaps list, and the Confidence_Band on the readiness screen.
5. THE Web_Client SHALL deliver a usable readiness result without any job source being configured.

---

### Requirement 47: Job dashboard and detail (RM-UI-002)

`Milestone: M9 · Priority: P0 · Depends on: RM-MATCH-003, RM-MATCH-004`

**User Story:** As a candidate facing hundreds of postings, I want a ranked list I can filter and drill into, so that I can spend my applications on the few jobs worth the effort rather than reading every description.

#### Acceptance Criteria

1. THE Web_Client SHALL display the count of analyzed postings and the count in each Match_Class.
2. THE Web_Client SHALL display a ranked list of postings ordered by descending overall match score within each Match_Class.
3. THE Web_Client SHALL display, per posting card, the company, the title, the match score, the Match_Class, up to three top match reasons, and up to three gaps.
4. WHEN the user opens a posting, THE Web_Client SHALL display the dimension breakdown, the matched evidence, the unmet required list, the unmet preferred list, the Confidence_Band, and the apply URL.
5. THE Web_Client SHALL allow filtering the result set by Match_Class, location, work mode, and posting age.
6. THE Web_Client SHALL open every apply URL as an external link and SHALL exclude any in-product application submission.

---

### Requirement 48: Journey integrity (RM-UI-003)

`Milestone: M9 · Priority: P0 · Depends on: RM-REV-001, RM-UI-001`

**User Story:** As a candidate, I want results marked stale the moment I edit my profile, so that I never compare a new profile against job classifications computed from the old one.

#### Acceptance Criteria

1. THE Web_Client SHALL enforce the step order upload, review, target selection, readiness, job results, and SHALL disable a step until its prerequisites are satisfied.
2. WHEN the user edits the Candidate_Profile after a readiness score has been produced, THE Web_Client SHALL mark the existing readiness and job results as stale and SHALL require recomputation before displaying them as current.
3. IF a Session expires, THEN THE Web_Client SHALL display an expiry message and SHALL return the user to the upload step.
4. THE Web_Client SHALL allow the user to return to the review step from any later step without re-uploading the resume, while the Session is valid.

---

**12 · Cross-Cutting Requirements**

### Requirement 49: API contracts (RM-API-001)

`Milestone: M0 · Priority: P0 · Depends on: none`

**User Story:** As an open-source contributor, I want one published schema and generated client types across clean module boundaries, so that I can change one component without discovering at runtime that another one relied on an undocumented field shape.

#### Acceptance Criteria

1. THE Backend_API SHALL define every request and response body as a Pydantic model and SHALL publish an OpenAPI document.
2. THE Backend_API SHALL validate every request body against its schema and SHALL return HTTP 422 with a field-level error list on failure.
3. THE Backend_API SHALL return a machine-readable error code and a human-readable message for every error response.
4. THE Backend_API SHALL version its HTTP interface with a path prefix.
5. THE Web_Client SHALL generate its API types from the published OpenAPI document.
6. THE Backend_API SHALL define module boundaries such that resume, privacy, rubric, job, matching, and LLM concerns are separately importable units with no cyclic dependency between them.
7. THE Backend_API SHALL be a single deployable service in v1 and SHALL exclude a microservice split.

---

### Requirement 50: Session and storage strategy (RM-SESS-001)

`Milestone: M0 · Priority: P0 · Depends on: RM-PRIV-001`

**User Story:** As a privacy-conscious candidate, I want my analysis to live in one bounded session with no account behind it, so that closing the tab ends the workflow instead of leaving my resume in a profile I cannot delete.

#### Acceptance Criteria

1. THE Backend_API SHALL identify each analysis workflow with an opaque Session token containing no Candidate_Data.
2. THE Session_Store SHALL hold Candidate_Data in process memory or an equivalent bounded store, subject to the retention limit in RM-PRIV-001.
3. THE Web_Client SHALL store client-side workflow state in `sessionStorage` and SHALL exclude `localStorage` and IndexedDB for Candidate_Data in v1.
4. THE Web_Client SHALL describe `sessionStorage` as session-scoped browser storage and SHALL exclude any description of it as "never stored".
5. THE Backend_API SHALL exclude a separate cache service such as Redis from v1 unless a recorded decision establishes the need.
6. THE Backend_API SHALL exclude user accounts, authentication, and cross-session candidate history from v1.

---

### Requirement 51: Upload security (RM-SEC-001)

`Milestone: M1 · Priority: P0 · Depends on: RM-ING-001`

**User Story:** As a privacy-conscious candidate, I want uploads parsed with remote entity loading and embedded scripts disabled, so that another user's crafted PDF cannot read files off the server or stall it with a compression bomb while my own resume is in memory.

#### Acceptance Criteria

1. THE Upload_Service SHALL treat every uploaded file as untrusted input.
2. THE Upload_Service SHALL parse uploads with external entity resolution, remote resource loading, and embedded script execution disabled in the extraction libraries.
3. IF extraction of a single document exceeds a configured wall-clock limit, THEN THE Upload_Service SHALL abort the extraction and SHALL return error code `EXTRACTION_TIMEOUT`.
4. THE Upload_Service SHALL apply a configured limit on decompressed document size to reject compression-bomb inputs.
5. THE Upload_Service SHALL exclude the uploaded filename from any filesystem path it constructs, using a generated identifier instead.

---

### Requirement 52: Service security baseline (RM-SEC-002)

`Milestone: M0 · Priority: P0 · Depends on: RM-API-001`

**User Story:** As an operator, I want origins restricted, secrets read from the environment, and rate limits on the paid endpoints, so that a committed API key or an unthrottled upload loop does not become an incident or an unexpected model bill.

#### Acceptance Criteria

1. THE Backend_API SHALL restrict cross-origin requests to an explicit allow-list of origins supplied by configuration.
2. THE Backend_API SHALL read every secret and API key from environment configuration and SHALL exclude secrets from the repository, verified by a secret-scanning check in continuous integration.
3. THE Backend_API SHALL apply rate limiting per client to the upload endpoint and to every endpoint that triggers an LLM_Provider or Job_Source_Adapter request.
4. THE Backend_API SHALL provide a `.env.example` listing every required configuration key with placeholder values.
5. THE Backend_API SHALL serve over HTTPS in every non-local deployment.
6. IF a required configuration key is absent at startup, THEN THE Backend_API SHALL fail to start and SHALL report the missing key name.

---

### Requirement 53: Dependency hygiene (RM-SEC-003)

`Milestone: M0 · Priority: P1 · Depends on: RM-SEC-002`

**User Story:** As a maintainer, I want pinned dependencies and a vulnerability scan on every pull request, so that a parsing library that handles untrusted resumes cannot pick up a compromised transitive version between releases.

#### Acceptance Criteria

1. THE repository SHALL pin every direct dependency to an exact version in a lock file.
2. THE continuous integration pipeline SHALL run a dependency vulnerability scan on every pull request and SHALL fail the build on a finding of high or critical severity.
3. THE continuous integration pipeline SHALL run static analysis, formatting, and type checking for both the Python and TypeScript codebases on every pull request.

---

### Requirement 54: Privacy-safe telemetry (RM-OBS-001)

`Milestone: M0 · Priority: P0 · Depends on: RM-PRIV-001`

**User Story:** As an operator, I want an allow-listed set of metrics that carries no candidate content, so that I can see a rise in extraction failures or source errors without the observability stack becoming a second copy of everyone's resume.

#### Acceptance Criteria

1. THE Telemetry_Logger SHALL restrict recorded metrics to: extraction success and failure counts by error code, extraction duration, structuring duration, Job_Source_Adapter latency and error counts, postings fetched and normalized and rejected, scoring duration, scoring exception counts, LLM_Provider latency and error counts, ungrounded-statement counts, and fabrication-attempt counts.
2. THE Telemetry_Logger SHALL record a Session token only in hashed form.
3. THE Telemetry_Logger SHALL emit structured log records with an explicit field allow-list.
4. THE Backend_API SHALL expose a health endpoint reporting service status, loaded rubric count, and configured source count, containing no Candidate_Data.

---

### Requirement 55: Log content prohibitions (RM-OBS-002)

`Milestone: M0 · Priority: P0 · Depends on: RM-OBS-001`

**User Story:** As a privacy-conscious candidate, I want my name, contact details, and resume text kept out of every log line and stack trace, so that the retention promise is not undone by an exception message sitting in a log store for a year.

#### Acceptance Criteria

1. THE Telemetry_Logger SHALL exclude Raw_Resume_Bytes, Extracted_Text, Structured_Resume content, Candidate_Profile content, and Sanitized_Resume content from every log record, metric label, and trace attribute.
2. THE Telemetry_Logger SHALL exclude every value detected as PII under RM-PRIV-002 from every log record.
3. THE Telemetry_Logger SHALL exclude full prompt bodies and full model responses containing candidate-derived content from every log record, recording a content hash and a field-name list instead.
4. IF an exception message would contain candidate-derived content, THEN THE Backend_API SHALL replace the content with a redaction marker before the message is logged.
5. THE Telemetry_Logger SHALL exclude the client-supplied filename from every log record.
6. RM-TEST-001 SHALL include a test that runs the pipeline with a resume fixture containing distinctive marker strings and asserts that no marker string appears in captured log output.

---

### Requirement 56: Performance budgets (RM-PERF-001)

`Milestone: M1 (extraction), M8 (matching) · Priority: P1 · Depends on: RM-PARSE-001, RM-MATCH-001`

**User Story:** As a candidate, I want each step to finish in seconds and tell me which stage is running, so that I do not abandon the analysis mid-flow believing it has hung.

Budgets are stated as assumption AS-09 and are measured on the reference hardware profile recorded in the design phase.

#### Acceptance Criteria

1. WHEN a document of at most 5 MB and at most 10 pages is uploaded, THE Backend_API SHALL complete extraction and structuring within 5 seconds at the 95th percentile.
2. WHEN a Candidate_Profile and a Role_Rubric are supplied, THE Rubric_Engine SHALL return a readiness result within 500 milliseconds at the 95th percentile.
3. WHEN 200 Job_Posting records are supplied, THE Matching_Engine SHALL return the complete ranked result set within 3 seconds at the 95th percentile.
4. WHILE a long-running operation is in progress, THE Web_Client SHALL display a progress indicator naming the current pipeline stage.
5. THE continuous integration pipeline SHALL measure criteria 1 to 3 against fixture inputs and SHALL fail the build when a measured p95 exceeds its budget by more than 50 percent.

---

### Requirement 57: Accessibility (RM-A11Y-001)

`Milestone: M2 onward · Priority: P1 · Depends on: RM-UI-001`

**User Story:** As a candidate who navigates by keyboard and screen reader, I want to correct my parsed profile and read every score, Match_Class, and error without relying on colour or a pointer, so that the tool is usable to me rather than only inspectable.

#### Acceptance Criteria

1. THE Web_Client SHALL make every interactive control operable by keyboard alone, including the Profile_Review_UI editing controls.
2. THE Web_Client SHALL provide an accessible name for every form control, button, and link.
3. THE Web_Client SHALL meet a contrast ratio of at least 4.5 to 1 for normal-size text and 3 to 1 for large text.
4. THE Web_Client SHALL convey score, Match_Class, and Confidence_Band information through text or a text alternative in addition to colour.
5. WHEN a validation error or pipeline error occurs, THE Web_Client SHALL announce the error to assistive technology through a live region.
6. THE continuous integration pipeline SHALL run automated accessibility checks against the primary screens and SHALL fail the build on a violation of WCAG 2.1 level AA rules detectable by the automated tooling.
7. THE project SHALL document that automated checks are partial and that full WCAG conformance requires manual assistive-technology testing and expert review.

---

### Requirement 58: Test strategy and build gates (RM-TEST-001)

`Milestone: M0 onward · Priority: P0 · Depends on: RM-API-001`

**User Story:** As a maintainer, I want the privacy, cloud-boundary, and fabrication gates to fail the build with no override, so that a regression in the guarantees the product is sold on cannot be merged by a reviewer who did not know they existed.

#### Acceptance Criteria

1. THE continuous integration pipeline SHALL run the Python test suite with pytest and the frontend unit and integration suites on every pull request, and SHALL fail the build on any failure.
2. THE test suite SHALL cover, as distinct areas: resume parsing, PII detection and sanitization, the rubric engine, requirement extraction, matching and classification, job source adapters, and the LLM layer.
3. THE test suite SHALL include property-based tests for the round-trip, idempotence, determinism, and invariant properties stated in RM-PARSE-004, RM-SKILL-001, RM-RUB-001, RM-EVID-001 (including the item-order-permutation determinism property of criterion 6), RM-SCORE-001 criterion 12, RM-SCORE-002, RM-SCORE-003, RM-MATCH-001 criterion 7, RM-MATCH-004, RM-MATCH-005, RM-JOB-001, RM-PRIV-003 (including the sanitization idempotence property of criterion 7), and RM-CONF-001 (including the determinism property of criterion 5).
4. THE test suite SHALL include integration tests, rather than property-based tests, for outcomes that depend on external services or on configuration presence.
5. THE test suite SHALL include Playwright end-to-end coverage of the First Closed Loop.
6. THE test suite SHALL replace every LLM_Provider and Job_Source_Adapter with a deterministic stub by default, and SHALL isolate live-network tests behind an explicit opt-in marker.
7. THE test suite SHALL include the privacy tests required by RM-PRIV-002 criterion 7, RM-PRIV-003 criteria 6, 7, and 11, RM-PRIV-005 criterion 6, and RM-OBS-002 criterion 6, and the fabrication-pressure suite required by RM-COACH-002 criteria 8 and 9.
8. THE continuous integration pipeline SHALL fail the build when a privacy test, a PII detection gate under criterion 9, a requirement-extraction accuracy gate under criterion 10, a cloud-boundary choke-point check under criterion 11, or a fabrication-pressure test under criterion 12 fails, and SHALL provide no override path for any of them.
9. THE continuous integration pipeline SHALL evaluate the PII detection gates of RM-PRIV-002 criterion 7 on every pull request and SHALL fail the build, reporting the affected category and the failing figure, when per-category recall for any category named in RM-PRIV-002 criterion 2 falls below the threshold of RM-PRIV-002 criterion 6, when the labeled privacy fixture corpus contains fewer than 20 labeled instances for any such category, or when per-category precision for any such category falls more than 0.05 below the figure recorded for the previous release.
10. THE continuous integration pipeline SHALL measure requirement-extraction accuracy against the hand-labeled posting sample of AS-05 and SHALL fail the build, reporting the failing figure, when precision on the `required` class falls below 0.90 or agreement across the `required`, `preferred`, and `contextual` classes falls below 0.80, per RM-REQX-001 criterion 11.
11. THE continuous integration pipeline SHALL run the cloud-boundary choke-point check of RM-PRIV-003 criterion 11 on every pull request and SHALL fail the build when any Backend_API component other than the LLM_Gateway references the LLM_Provider interface or performs outbound transmission across the Cloud_Boundary, and the test suite SHALL include the stub-provider zero-invocation assertions for requests rejected under RM-PRIV-003 criteria 3, 5, and 10.
12. THE test suite SHALL include the fabrication-pressure suite of RM-COACH-002 criteria 8 and 9, covering at least 20 profile-posting pairings across all five reference roles and at least 10 deterministic LLM_Provider stub responses spanning the enumerated fabrication forms, and SHALL assert the permitted-claim, numeric-token, `do_not_claim`, and fabrication-attempt-event obligations stated there.

---

### Requirement 59: Fixture corpus (RM-TEST-002)

`Milestone: M1 · Priority: P0 · Depends on: RM-TEST-001`

**User Story:** As an open-source contributor, I want checked-in resumes, postings, and expected-output baselines that carry no real personal data, so that I can see whether my change to parsing or scoring altered a result before a reviewer has to guess.

#### Acceptance Criteria

1. THE repository SHALL contain a version-controlled resume fixture corpus including: a single-column PDF, a two-column PDF, a table-based PDF, a text-box PDF, a multi-page PDF, a DOCX, a document with missing sections, a document with duplicate headings, a document with unusual section headings, a malformed-encoding document, and an image-only PDF.
2. THE resume fixture corpus SHALL contain synthetic or explicitly consented documents only, and SHALL contain no real third-party personal data.
3. THE repository SHALL contain a labeled PII fixture corpus covering every category in RM-PRIV-002 criterion 2, including international phone formats and near-miss strings that must not be redacted.
4. THE repository SHALL contain a Job_Posting fixture set including a complete posting, a posting with no requirement language, a posting with conflicting experience figures, a duplicate posting pair, a posting with missing fields, and a malformed source response.
5. THE repository SHALL contain candidate profile fixtures representing: a strong candidate for each of the five reference roles, a mismatched candidate, an overqualified candidate, and an empty profile.
6. THE repository SHALL contain the expected-output baselines for the fixtures in criterion 5, so that scoring regressions are detectable.

---

### Requirement 60: Contributor extensibility (RM-EXT-001)

`Milestone: M4 (rubrics), M6 (sources) · Priority: P1 · Depends on: RM-RUB-001, RM-JOB-002`

**User Story:** As an open-source domain expert, I want to contribute a role rubric or a job source without modifying the scoring engine, so that my contribution is reviewable and low-risk.

#### Acceptance Criteria

1. WHEN a contributor adds a valid Role_Rubric file, THE Backend_API SHALL make the role available for readiness scoring without any change to Python source files.
2. WHEN a contributor adds a Source_Registry entry for an existing source identifier, THE Backend_API SHALL ingest from that organization without any change to Python source files.
3. THE repository SHALL document the Role_Rubric schema, the alias file format, the Source_Registry format, and the Job_Source interface with a worked example for each.
4. THE continuous integration pipeline SHALL validate every Role_Rubric file, the alias file, and the Source_Registry on every pull request and SHALL fail the build on a validation error.
5. THE Backend_API SHALL exclude community-supplied executable code from runtime loading in v1, restricting configuration contributions to declarative data files.

---

### Requirement 61: Rubric and ontology versioning (RM-EXT-002)

`Milestone: M4 · Priority: P1 · Depends on: RM-RUB-002`

**User Story:** As a candidate, I want to be told when the rubric scoring me is still a draft and which version produced my result, so that I weigh an unvalidated judgement accordingly instead of treating it as settled.

#### Acceptance Criteria

1. THE Role_Rubric schema SHALL require a version identifier and a status of `draft`, `reviewed`, or `stable`.
2. THE Rubric_Loader SHALL expose the rubric version and status in every readiness response.
3. WHILE a Role_Rubric has status `draft`, THE Web_Client SHALL display a notice that the rubric is unvalidated.
4. THE alias file SHALL carry a version identifier that is reported alongside every readiness and match result.
5. THE repository SHALL record, per Role_Rubric, the basis for its weights, so that a reviewer can distinguish expert judgement from job-market observation.

---

### Requirement 62: Containerized development and deployment (RM-DEP-001)

`Milestone: M0 · Priority: P1 · Depends on: RM-API-001`

**User Story:** As an open-source contributor, I want one documented command to bring up the whole loop from a clean checkout with fixtures and no model key, so that my first evening on the project is spent on the code rather than on environment setup.

#### Acceptance Criteria

1. THE repository SHALL contain a Dockerfile for the Backend_API and a Dockerfile for the Web_Client.
2. THE repository SHALL contain a Docker Compose configuration that starts the full application locally with the Fixture Job_Source_Adapter and no LLM_Provider configured.
3. WHEN the Docker Compose configuration is started from a clean checkout with the documented commands, THE application SHALL serve the First Closed Loop without additional manual setup.

---

### Requirement 63: Self-host and local model mode (RM-DEP-002)

`Milestone: M11 · Priority: P2 · Depends on: RM-DEP-001, RM-LLM-001`

**User Story:** As an operator running my own instance, I want a local model runtime whose failure degrades to deterministic results rather than silently reaching a cloud provider, so that my no-egress promise to users holds even when the local model is down.

#### Acceptance Criteria

1. THE repository SHALL contain a Docker Compose configuration that includes a local model runtime and configures it as the active LLM_Provider.
2. IF the local model runtime is unreachable, THEN THE Backend_API SHALL return the deterministic results with a `guidance_unavailable` state rather than falling back to a cloud LLM_Provider.
3. THE repository SHALL document the resource requirements of the local mode and the quality tradeoff relative to the cloud LLM_Provider.

---

## Definition of Done

A requirement is complete when all of the following hold. This applies at the requirement level, and a milestone is complete when every mapped requirement is complete.

1. Every SHALL criterion is implemented.
2. Every criterion is covered by an automated test or a named inspectable artifact, and the tests pass in continuous integration.
3. Error and failure paths named in the criteria are handled and tested.
4. Privacy impact is checked against RM-PRIV-001 through RM-PRIV-005, and no new code path writes Candidate_Data to a persistent store or crosses the Cloud_Boundary outside the LLM_Gateway.
5. Public interfaces and configuration formats introduced by the requirement are documented.
6. No scope beyond the requirement's criteria was added.
7. Any deviation from a criterion is recorded as an amendment to this document before merge.

---

## Assumptions

Assumptions are explicit, unvalidated, and changeable. Each names how it would be validated.

- **AS-01 · Web-first delivery.** ResumeMatch is a web application. Native mobile, desktop, and browser-extension form factors are excluded from v1. *Validation: user feedback on the first public release.*
- **AS-02 · Technology stack.** Next.js, React, and TypeScript on the frontend; Python, FastAPI, and Pydantic on the backend; pytest and Playwright for testing; Docker and Docker Compose for packaging. *Validation: M0 completion without material friction.*
- **AS-03 · Server-side pipeline.** Extraction, structuring, sanitization, and scoring execute in the Backend_API rather than in the browser, because the Python document-parsing and PII-detection ecosystem is the reason for choosing Python. This is what makes the ideation document's Mode A unprovable by default (conflict C-2). *Validation: prototype comparison of browser-side extraction quality against the fixture corpus.*
- **AS-04 · Five reference roles are sufficient to prove generality.** One role per domain, sharing one scoring code path, demonstrates config-driven extensibility; they are an architecture-validation set, not a complete catalogue. *Validation: RM-RUB-003 criterion 7 plus contributor addition of a sixth role without code change.*
- **AS-05 · Deterministic requirement extraction is adequate for v1.** Pattern-based required/preferred classification is good enough for the First Closed Loop. *Validation: at least 0.90 precision on the `required` class and at least 0.80 agreement across the `required`, `preferred`, and `contextual` classes, measured against a hand-labeled sample of at least 100 Job_Posting records, gated in continuous integration per RM-REQX-001 criterion 11 and RM-TEST-001 criterion 10; failing either figure is what reopens OD-06.*
- **AS-06 · Reduced evidence ladder.** The 0–5 ladder is reduced to four levels plus a `quantified_impact` flag because levels such as "internship" and "professional ownership" cannot be reliably distinguished from resume structure alone. *Validation: agreement rate between assigned levels and human labeling on the profile fixtures; see OD-18.*
- **AS-07 · Match dimension weights are unvalidated.** The weights in RM-MATCH-001 are carried from the handoff as a starting point, not as a validated model. *Validation: rank-order agreement against domain-expert rankings of at least 50 candidate-job pairs per reference role, plus sensitivity analysis showing which weight changes alter Match_Class.*
- **AS-08 · Classification thresholds are unvalidated.** The proposed 75 and 55 thresholds are placeholders. *Validation: threshold sweep against the expert-ranked pairs from AS-07, selecting thresholds that maximize agreement on the `skip` boundary, since a false `skip` costs the user an opportunity.*
- **AS-09 · Performance budgets.** The budgets in RM-PERF-001 are estimates for a single-instance deployment on modest hardware. *Validation: measurement against the fixture corpus during M1 and M8.*
- **AS-10 · Session lifetime.** A 24-hour maximum retention with no cross-session history is sufficient for a single analysis workflow. *Validation: observed abandonment and resume-re-upload rates.*
- **AS-11 · Seed source coverage.** A seeded Source_Registry can produce at least 100 relevant postings across the five reference role families. Live-source coverage validation is a P1 activity under RM-JOB-003 criterion 6 and is not a First Closed Loop gate; the First Closed Loop is validated against the Fixture_Job_Set through the Fixture Job_Source_Adapter. *Validation: measured ingestion counts against live sources at M6, as a P1 obligation.*
- **AS-12 · No embeddings needed in v1.** Deterministic normalization plus an alias file replaces semantic similarity for skill and title matching. *Validation: measured unmapped-skill rate from RM-SKILL-001 criterion 3; a persistently high rate reopens OD-12.*
- **AS-13 · Requirement unit delimitation.** The list-item-and-sentence delimitation rule in RM-REQX-001 criterion 9, including the 400-character clause split, is a v1 heuristic and not a validated parsing model. *Validation: measured against the hand-labeled sample in AS-05, reporting the rate at which a delimited unit splits or merges a requirement a human would have read as one.*
- **AS-14 · Disqualification thresholds.** The unmet-required threshold of 2 and the seniority tolerance of 2 years in RM-MATCH-002 criteria 3 and 4 are unvalidated. *Validation: swept against the expert-ranked pairs of AS-07 and AS-08, weighting a false `skip` more heavily than a false `stretch`, since a false `skip` costs the user an opportunity they would not otherwise see.*
- **AS-15 · Role-family equivalence and domain mapping.** The role-family equivalence table and the company-to-domain mapping in RM-MATCH-001 criteria 10 and 11 are hand-authored and cover only the five reference role families. Pairs absent from either table score 0, which biases match scores downward for unmapped roles and companies rather than treating them as neutral. *Validation: measure the unmapped-pair rate over ingested postings at M6; a high rate means the downward bias is affecting real results and the neutral-score alternative must be reconsidered; see OD-23.*
- **AS-16 · Evidence Level 3 gating.** The Level 3 conditions in RM-EVID-001 criteria 9 and 10, including the 20-skill demotion rule, are anti-gaming heuristics rather than measured discriminators. *Validation: agreement rate against human labeling on the candidate profile fixtures of RM-TEST-002 criterion 5.*
- **AS-17 · PII classification confidence floor.** The 0.80 minimum classification confidence in RM-PRIV-002 criterion 5 is unvalidated and directly trades recall against the retention of career evidence. *Validation: sweep the floor against the labeled privacy fixture corpus, holding per-category recall at or above the RM-PRIV-002 criterion 6 threshold while minimizing fail-safe redactions of Retain-default content.*

---

## Open Decisions

Each item states the question, the options, and a **proposed** default. A proposal is not a settled fact; it must be confirmed in the design phase or by the product owner before the dependent milestone begins.

The first sixteen items correspond to handoff section 36.

| ID | Question | Options | Proposal (unconfirmed) | Needed by |
|---|---|---|---|---|
| **OD-01** | Exact reference role per initial domain, given the two documents' differing SWE and Marketing titles | Handoff titles vs ideation titles | **Resolved by product owner:** Backend Engineer — Intern / New Grad; Financial Analyst (entry); Embedded Software / Firmware Engineer (intern/entry); Performance Marketing Analyst — Entry; Supply Chain Analyst (entry). These five are the reference architecture-validation set, not a closed catalogue. | Resolved |
| **OD-02** | Initial cloud LLM provider | Gemini, OpenAI, Anthropic | Single provider chosen on structured-output reliability and free-tier availability; decision recorded before M10 | M10 |
| **OD-03** | Exact PII categories removed vs retained | See RM-PRIV-002 policy table | Adopt the RM-PRIV-002 table as the v1 default | M3 |
| **OD-04** | Do employer and university names cross the Cloud_Boundary | Always retain, always remove, user-selectable | Retain by default, with a user toggle that removes them and displays the resulting match-quality caveat | M3 |
| **OD-05** | First live ATS or job source | Greenhouse, Lever, Ashby, Adzuna, USAJobs | Greenhouse public boards, because the endpoint is stable and unauthenticated; Adzuna as the first universal-search adapter | M6 |
| **OD-06** | Deterministic, LLM, or hybrid job requirement extraction | Deterministic only, LLM only, hybrid | Deterministic for v1. RM-REQX-001 criterion 11 now sets measurable gates — at least 0.90 precision on the `required` class and at least 0.80 agreement across all three classes — and failing either gate is what triggers reconsideration of the hybrid LLM-assisted path; the gates are enforced in continuous integration per RM-TEST-001 criterion 10 | M7 |
| **OD-07** | Initial match dimension weights | See RM-MATCH-001 | Use the handoff weights as unvalidated defaults per AS-07 | M8 |
| **OD-08** | Strong Apply / Stretch / Skip thresholds | Any configured pair | 75 and 55, unvalidated per AS-08 | M8 |
| **OD-08b** | Whether to reintroduce a fourth `apply` band | Three bands, four bands | Ship three bands per conflict C-1; revisit after user feedback on whether `stretch` is too broad | Post-v1 |
| **OD-09** | Job caching strategy | No cache, in-process cache, relational store, search index | Relational store for Public_Job_Data with a configured maximum posting age; no search index in v1 | M6 |
| **OD-10** | Browser state and storage approach | `sessionStorage`, `localStorage`, IndexedDB, server-session only | `sessionStorage` plus a server-side Session, per RM-SESS-001 | M0 |
| **OD-11** | Deployment platform | Container host, platform-as-a-service, self-host only | Container-based hosted deployment plus a documented self-host path; specific provider deferred | Pre-v1 release |
| **OD-12** | Whether embeddings are needed at all in v1 | Yes, no | No, per AS-12 | M8 |
| **OD-13** | Rubric validation method | Expert review, job-market frequency analysis, both | Both: expert review for weights, frequency analysis over ingested postings for signal lists | M4 |
| **OD-14** | Initial geography supported | One country, English-language postings, unrestricted | English-language postings, no geographic restriction beyond what the sources provide; location matching is user-constraint driven | M6 |
| **OD-15** | Finance sub-role taxonomy | Single Financial Analyst rubric vs a family | One entry-level Financial Analyst rubric in v1; taxonomy expansion post-v1 | M4 |
| **OD-16** | Hardware taxonomy boundaries across embedded software, firmware, electronics, FPGA, verification, and digital design | Single combined rubric vs split rubrics | One combined embedded-software/firmware rubric in v1; the other five treated as post-v1 roles | M4 |
| **OD-17** | Repository structure | Handoff section 23 layout vs ideation section 32 monorepo layout | Not proposed here; decide in the design phase against the module boundaries in RM-API-001 criterion 6 (conflict C-3) | Design phase |
| **OD-18** | Whether to restore the full 0–5 evidence ladder | Four levels (v1) vs five or six levels | Keep four levels per AS-06 until labeling data shows the finer distinctions are inferable | Post-v1 |
| **OD-19** | How Opportunity_Gain is validated, given no ground truth | User-reported outcomes with consent, expert review, no validation and label as estimate only | Label as an estimate and validate only the frequency component; defer the counterfactual component | M12 |
| **OD-20** | Whether a user may bypass the profile review step | Mandatory review vs optional | Mandatory per RM-REV-001 criterion 1; revisit only if measured friction is high | M2 |
| **OD-21** | Whether OCR is added for scanned resumes | Never, post-v1 optional, post-v1 default | Post-v1 optional; v1 fails safely per RM-PARSE-002 | Post-v1 |
| **OD-22** | The configured relevance rule that admits Candidate_Profile experience entries into `Total_Relevant_Experience` (RM-MATCH-002 criterion 8) | All dated experience; only experience matching the target role family; only experience matching the target domain | All dated experience for v1, because a narrower rule increases false `skip` under RM-MATCH-002 criterion 4, and a false `skip` is the costliest error class | M8 |
| **OD-23** | Whether the role-family equivalence table and the company-to-domain mapping (RM-MATCH-001 criteria 10 and 11) are hand-authored or derived from ingested postings, and whether an absent pair scores 0 or a neutral mid-range value | Hand-authored with 0 for absent pairs; hand-authored with a neutral default; derived from ingested posting frequency | Hand-authored covering the five reference role families for v1, with the absent-pair scoring revisited against AS-15's measured unmapped-pair rate | M8 |
| **OD-24** | The per-category placeholder token forms used for PII removal (RM-PRIV-002 criterion 9), and whether a placeholder indicates the removed category to the LLM_Provider | An opaque uniform token; a category-labelled token; a category-labelled token carrying no length or content information | A category-labelled token carrying no length or content information, since the category label improves explanation quality while the omission of length prevents inference about the removed value | M3 |

---

## Non-Goals

ResumeMatch v1 explicitly does not include:

1. Authentication, user accounts, or persistent candidate history.
2. Automated or assisted job application submission, and cover letter generation.
3. LinkedIn or Indeed scraping, and any scraping prohibited by a site's terms.
4. Optical character recognition for scanned or image-only resumes.
5. A vector database, embeddings, or semantic similarity search.
6. Native mobile applications, desktop applications, and browser extensions.
7. A fixed or closed role catalogue, and more than one seniority band per reference role. Additional schema-conforming Role_Rubric configurations are permitted only when explicitly planned; they are not automatically part of the First Closed Loop.
8. Global or comprehensive job market coverage.
9. Recruiter-facing features, applicant tracking functionality, and candidate sourcing.
10. Salary prediction, offer probability, hiring outcome prediction, and any claim of hiring certainty.
11. Personality, psychometric, or behavioural assessment.
12. Social features, sharing, and public profiles.
13. Microservice decomposition, message queues, and multi-region infrastructure.
14. Complex analytics infrastructure, data warehousing, and business intelligence dashboards.
15. Fine-tuned or self-trained models.
16. Multiple cloud LLM providers.
17. Community-supplied executable plugins loaded at runtime.
18. Opportunity Gain in the First Closed Loop, and its counterfactual component in v1.

---

## Traceability Notes for the Design Phase

The design phase must, at minimum, resolve:

- The module and directory layout (OD-17), consistent with the boundaries in RM-API-001 criterion 6.
- The concrete Role_Rubric schema fields and their JSON Schema, satisfying RM-RUB-001.
- The Evidence_Level-to-weight mapping referenced by RM-SCORE-001 criterion 3 and RM-MATCH-001 criterion 3.
- The required-language and preferred-language pattern sets referenced by RM-REQX-001.
- The Job_Source interface signature and the Fixture adapter's file format, satisfying RM-JOB-002.
- The LLM_Provider operation signatures and response schemas, satisfying RM-LLM-001 and RM-LLM-003.
- The configured omission priority order applied to budget-driven request reduction, and the set of candidate-derived field paths ineligible for omission because an operation's response schema requires them (RM-LLM-003 criterion 6).
- The concrete confidence weights referenced by RM-CONF-001.
- The reference hardware profile for RM-PERF-001.
- The version-controlled unit list and the proficiency-word exclusion list (RM-EVID-001 criteria 3 and 7).
- The required-language, preferred-language, and contextual-language pattern sets, and the delimitation rule set (RM-REQX-001 criteria 2, 3, 4, and 9).
- The role-family equivalence table and the company-to-domain mapping (RM-MATCH-001 criteria 10 and 11).
- The per-category placeholder token constants (RM-PRIV-002 criterion 9).
- The closed reason-code enumeration and its deterministic ordering (RM-MATCH-003 criteria 9 and 10).
- The configured relevance rule for `Total_Relevant_Experience` (RM-MATCH-002 criterion 8).
- The configured Candidate_Profile section list and the dimension-to-field mapping used by the confidence denominators (RM-CONF-001 criterion 9).
- The architectural mechanism that makes the LLM_Gateway choke point structurally enforceable rather than a matter of convention, sufficient to satisfy the build-failing check in RM-PRIV-003 criterion 11.

Every design decision must cite the requirement IDs it satisfies, and every task must cite the requirement IDs it implements. Where implementation reveals that a criterion is wrong or unachievable, this document is amended first and the reason recorded, per the source-of-truth hierarchy in handoff section 25.
