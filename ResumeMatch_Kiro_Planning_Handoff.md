# ResumeMatch — Kiro Planning Handoff

> **Purpose:** Give this file to Kiro before implementation. Kiro should use it to create the project's planning/specification files, including requirements, architecture/design, tasks, steering rules, testing strategy, privacy model, and roadmap.
>
> **Important:** This is not the final `requirements.md`. It is the authoritative planning input from which Kiro should create implementation-ready specifications.

---

## 1. Product Definition

**Working name:** ResumeMatch

ResumeMatch is a privacy-first, open-source **job application decision engine**.

The product should answer:

> **Which jobs am I actually competitive for, why, and what should I improve next?**

A user uploads a resume, selects a target role, and ResumeMatch:

1. Parses the resume into structured data.
2. Lets the user correct parsing mistakes.
3. Detects/removes PII before cloud-AI use.
4. Evaluates candidate readiness using deterministic, role-specific rubrics.
5. Retrieves relevant jobs from legitimate APIs/public ATS endpoints.
6. Normalizes job descriptions and requirements.
7. Ranks candidate-job fit.
8. Classifies jobs as **Strong Apply / Stretch / Skip**.
9. Explains strengths, gaps, and hard-requirement failures.
10. Suggests truthful resume/application improvements.
11. Eventually estimates which missing skills unlock the most additional opportunities.

The product is **not just a resume grader**.

---

## 2. Initial Domains

The architecture must be extensible across:

- Software Engineering
- Finance
- Embedded Systems / Hardware
- Marketing
- Supply Chain / Operations

Do **not** build dozens of roles initially.

Validate the architecture with approximately one representative role per domain:

| Domain | Initial role |
|---|---|
| Software Engineering | Backend / Software Engineer |
| Finance | Financial Analyst |
| Embedded / Hardware | Embedded Software Engineer |
| Marketing | Digital Marketing Analyst |
| Supply Chain / Operations | Supply Chain Analyst |

Future roles should mostly be added through configuration rather than rewriting core logic.

---

## 3. Core Product Principles

### 3.1 Privacy First

Resume files must not be persistently stored by ResumeMatch servers.

Distinguish between:

- raw resume bytes
- extracted text
- structured resume
- sanitized resume
- candidate profile
- session state
- public job data

Avoid unprovable claims like "nothing ever touches disk."

Preferred public wording:

> **Resume files are not persistently stored by ResumeMatch servers.**

Raw resume bytes should be released/discarded after extraction wherever technically practical.

### 3.2 Deterministic Scoring

LLMs must **not** be the authority for numeric readiness or job-match scores.

```text
Resume Evidence + Role Rubric
            ↓
Deterministic Scoring Engine
            ↓
Readiness / Match Score
```

LLMs may explain scores, extract ambiguous information, summarize gaps, and coach the user.

### 3.3 Evidence-Based Recommendations

Recommendations should cite evidence from:

- the candidate resume/profile
- the selected rubric
- job descriptions
- aggregated job-market demand

Bad:

> Learn SQL.

Better:

> SQL appears in 61% of the currently relevant roles and is not evidenced in your resume.

### 3.4 No Fabricated Experience

ResumeMatch must never encourage the user to claim:

- skills they do not have
- work they did not perform
- certifications they do not possess
- projects they did not complete
- fake quantified impact

This rule must exist in requirements, prompts, tests, acceptance criteria, and agent steering files.

### 3.5 Explainability

Important scores must expose:

- contributing factors
- evidence used
- missing evidence
- hard vs preferred requirements
- confidence where appropriate

Avoid unexplained "84% match" outputs.

---

## 4. Recommended Product Form

Build ResumeMatch as a **web application first**.

Do not begin with:

- native mobile
- desktop application
- browser extension

Later, Docker/self-host mode can provide a fully local experience.

---

## 5. Recommended Technology Direction

Kiro may refine details if justified, but plan around:

### Frontend
- Next.js
- React
- TypeScript

### Backend
- Python
- FastAPI
- Pydantic

### Testing
- pytest
- frontend unit/integration tests
- Playwright for important end-to-end flows

### Deployment
- Docker
- Docker Compose for local/self-host mode
- hosted deployment later

### AI
Architect a provider interface.

Eventually support:
- one cloud provider first
- Ollama/local mode
- OpenAI / Claude / Gemini or others later

Do not implement every provider in the first milestone.

---

## 6. High-Level Architecture

```text
Resume
  ↓
Resume Extraction
  ↓
Structured Resume
  ↓
PII Sanitizer
  ↓
Candidate Evidence
  ↓
Candidate Profile
  │
  ├─────────────→ Rubric Engine
  │                    ↓
  │              Readiness Score
  │
  ↓
Matching Engine
  ↑
Normalized Jobs
  ↑
Requirement Extraction
  ↑
Job Source Adapters
  ↑
ATS / Job APIs

LLM Layer:
- explains
- coaches
- performs bounded extraction when useful
- never owns deterministic scoring
```

Keep module boundaries explicit.

---

## 7. Resume Ingestion

Initially support:

- PDF
- DOCX

Responsibilities:

- validate MIME/type
- enforce size limits
- extract text
- detect extraction failure
- return parsing confidence where useful
- safely discard raw upload after use

Resume formats may contain:

- multiple columns
- tables
- text boxes
- strange reading order
- malformed encodings
- scanned/image-only PDFs

The first version does not need perfect OCR support.

---

## 8. Structured Resume Schema

Create a common candidate schema.

Conceptually:

```json
{
  "summary": "",
  "skills": [],
  "experience": [],
  "education": [],
  "projects": [],
  "certifications": [],
  "achievements": []
}
```

Where useful, extracted items should retain:

- original/source text
- normalized value
- confidence
- provenance/evidence location

A **Parsed Profile Review** screen is mandatory so users can correct parsing errors before scoring.

---

## 9. Privacy / PII Layer

Potential detection mechanisms:

- regex
- Microsoft Presidio
- heuristics
- optional NLP/LLM only where safe

Potential PII:

- name
- email
- phone
- physical address
- personal URLs
- LinkedIn
- GitHub
- student IDs
- other identifiers

Kiro must define which entities are removed versus retained.

Important ambiguity to resolve:

- company names
- universities
- certifications

These can be useful career evidence and are not necessarily equivalent to direct personal contact information.

### Desired Privacy Inspector

Before cloud AI receives data, the user should eventually be able to inspect:

```text
Sent to cloud AI
✓ Skills
✓ Experience descriptions
✓ Education level
✓ Projects

Removed
✗ Name
✗ Email
✗ Phone
✗ Address

[View sanitized payload]
```

---

## 10. Domain / Role Rubric System

Rubrics must be configuration-driven, preferably YAML or JSON.

Example concept:

```yaml
role: embedded_software_engineer

categories:
  programming:
    weight: 20
    signals:
      - C
      - C++
      - Python

  embedded_systems:
    weight: 25
    signals:
      - microcontrollers
      - RTOS
      - interrupts
      - peripherals

  protocols:
    weight: 15
    signals:
      - SPI
      - I2C
      - UART
      - CAN

  projects:
    weight: 20

  tools:
    weight: 10

  fundamentals:
    weight: 10
```

The schema should eventually support:

- categories
- weights
- required signals
- preferred signals
- alternate signals
- penalties
- experience bands
- seniority
- certifications
- projects
- tools
- education
- evidence confidence

Do not hardcode five unrelated scoring systems.

---

## 11. Candidate Readiness vs Job Match

These are separate metrics.

### Candidate Readiness

Question:

> How prepared is this candidate for the selected role family?

Inputs:
- candidate profile
- selected role rubric

Example:

```text
Embedded Software Engineer

Programming          85
Embedded Concepts    68
Protocols            72
Projects             82
Tools                54
Fundamentals         77

Overall              73
```

### Job Match

Question:

> How well does this candidate fit this specific job?

Dimensions may include:

- required skills
- preferred skills
- experience
- seniority
- role similarity
- education
- domain exposure
- location/work mode
- mandatory constraints

Starting conceptual weights only:

```text
30% Skills
20% Experience
15% Role Similarity
10% Seniority
10% Education
10% Location / Work Mode
 5% Domain Signals
```

Kiro must mark these as assumptions until validated.

---

## 12. Hard Requirements vs Preferences

Job parsing should distinguish:

```text
required:
- C++
- 2+ years experience

preferred:
- Python
- CAN
- Embedded Linux
```

Missing a preferred requirement should produce a smaller penalty.

Missing a true hard requirement may trigger:

- a major penalty
- warning
- hard-filter behavior where justified

Plain keyword overlap is insufficient.

---

## 13. Skill Normalization

Create a small extensible ontology/alias layer.

Examples:

```text
JS = JavaScript
React.js = React
MS Excel = Microsoft Excel
MCU = Microcontroller
SCM = Supply Chain Management
```

Conceptual representation:

```json
{
  "canonical_skill": "javascript",
  "aliases": ["JS", "JavaScript"],
  "category": "programming_language"
}
```

Do not build a huge ontology before validating the core workflow.

---

## 14. Job Data Strategy

Do not scrape LinkedIn or Indeed in v1.

Potential legitimate sources:

- Greenhouse public job boards
- Lever Postings API
- Ashby public job postings
- Adzuna
- USAJobs where relevant

Greenhouse/Lever/Ashby often expose company-specific boards, so ResumeMatch will need a **company/source registry** or similar ingestion mechanism.

Do not assume they provide universal job search.

---

## 15. Job Source Adapter Pattern

Design a common interface:

```text
JobSource
├── GreenhouseSource
├── LeverSource
├── AshbySource
├── AdzunaSource
└── FutureSource
```

Every adapter should emit a common `JobPosting`.

Conceptually:

```typescript
interface JobPosting {
  id: string
  source: string
  company: string
  title: string
  description: string
  location?: string
  remote?: boolean
  employmentType?: string
  applyUrl: string
  requiredSkills: string[]
  preferredSkills: string[]
  experienceMin?: number
  experienceMax?: number
  seniority?: string
  postedAt?: string
}
```

Kiro should define the exact canonical schema.

---

## 16. Job Normalization Pipeline

```text
ATS / Job API
      ↓
Raw Posting
      ↓
Source Adapter
      ↓
Normalized Text
      ↓
Requirement Extraction
      ↓
Skill Normalization
      ↓
Normalized JobPosting
      ↓
Matching Engine
```

The system must tolerate incomplete job descriptions and extraction uncertainty.

---

## 17. Strong Apply / Stretch / Skip

Instead of showing hundreds of unranked postings:

```text
137 jobs analyzed

Strong Apply        21
Stretch             38
Skip                78
```

Possible reasons for Skip:

- hard requirement failure
- severe seniority mismatch
- extreme skill mismatch
- incompatible location/work mode

Stretch may indicate:

- core requirements met
- some important preferred requirements missing
- slightly below target experience

Thresholds must be configurable and validated.

---

## 18. Application Coach

For a selected job, explain:

- why candidate matches
- strongest supporting resume evidence
- missing skills
- missing experience
- relevant bullets
- weaker/unrelated bullets
- job keywords absent from resume
- what to emphasize truthfully
- what not to claim

Example:

```text
Why you match
✓ C++
✓ Microcontroller project
✓ Computer architecture

Gaps
△ RTOS
△ CAN

Resume recommendations
1. Move embedded project higher.
2. Emphasize C++ implementation details already present.
3. Mention UART/SPI experience only if actually performed.
```

LLM output must be constrained by candidate evidence.

---

## 19. Opportunity Gain / Learning ROI

This is a future differentiator.

Instead of only:

> Missing skill: SQL

Show market relevance:

```text
SQL

Requested by:
61% of Data Analyst opportunities
43% of Risk Analyst opportunities
18% of Financial Analyst opportunities

Estimated Opportunity Gain: High
```

Possible future concept:

```text
Opportunity Gain =
jobs moving Skip → Stretch
+
jobs moving Stretch → Strong Apply
```

Plan it, but do not block the first usable product on it.

---

## 20. Main User Journey

```text
Landing
  ↓
Upload Resume
  ↓
Parse
  ↓
Review / Correct Parsed Profile
  ↓
Privacy Preview
  ↓
Choose Domain
  ↓
Choose Role
  ↓
Set Target Constraints
  ↓
Candidate Readiness
  ↓
Retrieve Jobs
  ↓
Rank Jobs
  ↓
Strong Apply / Stretch / Skip
  ↓
Open Job
  ↓
Application Guidance
```

---

## 21. Initial UI Areas

### A. Landing / Upload
- explanation
- upload
- privacy summary
- supported formats

### B. Parsed Profile Review
- skills
- experience
- projects
- education
- certifications
- correction controls

### C. Career Target
- domain
- role
- experience level
- location
- work mode

### D. Candidate Analysis
- readiness score
- category scores
- strengths
- gaps
- confidence/evidence

### E. Job Dashboard
- Strong Apply / Stretch / Skip counts
- ranked job cards
- match score
- strongest match reasons
- gaps
- apply link
- detailed job analysis

---

## 22. Session and Storage Strategy

Avoid persistent candidate/resume storage in the first product.

Possible state:

- browser session state
- short-lived backend memory
- short-TTL cache only if necessary

Do not add Redis without need.

Important:

- `sessionStorage` is session-based.
- IndexedDB is persistent browser storage.

Do not describe IndexedDB as "never stored."

Persistent **non-user** data may later include:

- ATS/company registry
- cached public jobs
- skill aliases
- rubrics
- ingestion metadata

Explicitly separate public job data from candidate/resume data.

---

## 23. Suggested Repository Structure

```text
resumematch/
├── README.md
├── requirements.md
├── architecture.md
├── AGENTS.md
├── .env.example
│
├── docs/
│   ├── ideation.md
│   ├── privacy.md
│   ├── scoring.md
│   ├── matching.md
│   ├── job-sources.md
│   └── decisions/
│
├── rubrics/
│   ├── swe/
│   ├── finance/
│   ├── embedded/
│   ├── marketing/
│   └── supply-chain/
│
├── frontend/
├── backend/
│   ├── resume/
│   ├── privacy/
│   ├── rubrics/
│   ├── jobs/
│   ├── matching/
│   └── llm/
├── tests/
└── docker/
```

Kiro may improve this layout but should document why.

---

## 24. Agentic Development Model

Two agentic coding systems are available:

- **Kiro**
- **Codex**

Both have MCPs configured.

### Kiro owns planning

Kiro should:

- create requirements
- define user stories
- create architecture/design specs
- define interfaces/contracts
- define acceptance criteria
- create steering rules
- maintain roadmap/milestones
- identify dependencies
- identify open decisions
- prevent scope creep
- review implementation against specs

### Codex owns implementation

Codex should:

- scaffold
- implement frontend/backend
- implement parsers
- implement privacy pipeline
- implement rubrics/scoring
- implement job adapters
- implement matching
- write tests
- debug
- Dockerize
- refactor against approved specs

Do not let both agents independently redesign the product.

---

## 25. Source-of-Truth Hierarchy

```text
Planning / Ideation Input
        ↓
requirements.md
        ↓
architecture / design
        ↓
technical contracts
        ↓
tasks / milestones
        ↓
implementation
```

If code conflicts with approved requirements, requirements win unless deliberately amended.

For material changes:

1. update spec
2. document reason
3. update tasks
4. modify code

---

## 26. Steering / AGENTS Rules

Kiro should generate an `AGENTS.md` and/or Kiro steering files containing at least:

1. Do not invent requirements silently.
2. Do not add frameworks without justification.
3. Do not implement outside the active milestone.
4. Do not persist raw resume content.
5. Never send raw PII to a cloud model.
6. LLMs never own authoritative numeric scoring.
7. Never fabricate candidate experience.
8. Scoring logic must be deterministic and testable.
9. Job sources must implement a shared adapter contract.
10. Role rubrics must conform to a shared schema.
11. Prefer small tasks/PRs.
12. Privacy and scoring require strong tests.
13. No LinkedIn/Indeed scraping in v1.
14. External integrations must be isolated behind interfaces.
15. Record important architecture decisions.
16. Do not over-engineer for hypothetical scale before validation.

---

## 27. Development Milestones

### Milestone 0 — Repository & Contracts
- frontend/backend scaffold
- core schemas
- lint/format
- CI
- environment config
- tests

### Milestone 1 — Resume Ingestion
- PDF
- DOCX
- validation
- extraction
- error handling
- `StructuredResume`
- tests

Do not add jobs/LLM/accounts yet.

### Milestone 2 — Resume Structuring
- sections
- experience
- education
- projects
- skills
- certifications
- confidence
- parsed-profile correction UI

### Milestone 3 — Privacy
- PII detection
- sanitization
- privacy lifecycle
- cloud-boundary tests
- sanitized-payload preview

No cloud LLM receives unsanitized resume data.

### Milestone 4 — Rubric Engine
- rubric schema
- loader
- deterministic scoring
- evidence links
- first role rubric

Then add one representative role for each of the five domains.

### Milestone 5 — Candidate Readiness
- domain/role selection
- category scoring
- strengths/gaps
- evidence/confidence

At this point ResumeMatch should already be useful without live job matching.

### Milestone 6 — Job Ingestion
- canonical `JobPosting`
- `JobSource` interface
- first ATS adapter
- company/source registry
- normalization
- duplicate handling
- tests

### Milestone 7 — Requirement Extraction
- required/preferred skills
- experience
- seniority
- education where applicable
- normalization
- confidence

### Milestone 8 — Matching
- deterministic match dimensions
- hard-requirement handling
- overall score
- Strong Apply / Stretch / Skip
- explanations
- tests

### Milestone 9 — Job Dashboard
- ranked results
- filters
- cards
- detailed view
- application links

### Milestone 10 — LLM Coach
- provider interface
- one cloud provider
- structured explanations
- application guidance
- hallucination safeguards
- output validation

### Milestone 11 — Local AI
- Ollama
- local mode
- Docker Compose
- fallback behavior

### Milestone 12 — Opportunity Gain
- aggregate demand signals
- high-ROI skill improvements
- opportunity-unlock estimates

---

## 28. First Demo Scope

The first impressive closed loop should be:

```text
Upload Resume
  ↓
Parse
  ↓
Correct Profile
  ↓
Choose Domain + Role
  ↓
Score Candidate
  ↓
Load Controlled Job Set
  ↓
Rank
  ↓
Strong Apply / Stretch / Skip
```

Do **not** block this on:

- authentication
- mobile app
- user accounts
- full local AI
- dozens of roles
- global job coverage
- autonomous applications
- vector databases
- massive analytics dashboards

---

## 29. Early Non-Goals

ResumeMatch v1 is not:

- an ATS
- recruiter software
- an auto-apply bot
- a LinkedIn automation system
- a resume hosting platform
- an interview platform
- a social network
- a guaranteed predictor of hiring outcomes
- a giant job scraper
- a full career marketplace

---

## 30. Major Risks to Plan For

### Parsing
Complex PDFs and weird document layouts.

Mitigate with:
- parser tests
- confidence
- correction UI
- safe failure

### PII leakage
Mitigate with:
- layered detection
- tests
- minimal cloud payloads
- privacy preview
- fail-safe behavior

### Rubric bias
Mitigate with:
- transparent weights
- versioned rubrics
- validation
- expert/community review
- no claim of hiring certainty

### Job data fragmentation
Mitigate with:
- adapter pattern
- organization registry
- multiple legitimate sources
- coverage disclosure

### LLM hallucination
Mitigate with:
- evidence-constrained prompts
- structured outputs
- deterministic factual layer
- validation
- "not found/unknown" behavior

### Scope creep
Mitigate with:
- milestone gates
- one role/domain
- one job source first
- core functionality before polish

---

## 31. Testing Areas

Kiro should produce a dedicated testing specification covering:

### Resume Parsing
- normal PDF
- two-column PDF
- DOCX
- missing sections
- malformed text
- duplicate headings

### Privacy
- email
- phone
- names
- addresses
- URLs
- false positives
- edge cases

### Rubric Engine
- determinism
- weight validation
- missing evidence
- alternate skills
- penalties
- confidence

### Matching
- perfect fit
- underqualified
- overqualified
- hard requirement missing
- preferred requirement missing
- seniority mismatch
- location mismatch

### Job Sources
- normal response
- API failure
- rate limit
- malformed posting
- duplicate posting
- missing fields

### LLM
- valid structured output
- invalid JSON
- hallucinated skill
- timeout
- provider failure
- Ollama unavailable

---

## 32. Security / Observability

Plan baseline security:

- file size limits
- MIME/type validation
- filename sanitization
- malicious/untrusted upload handling
- request validation
- rate limiting
- secret management
- CORS
- dependency scanning

Privacy-safe telemetry may include:

- parser success/failure
- source API latency
- job counts
- adapter errors
- model latency
- scoring exceptions

Avoid logging:

- raw resume
- raw PII
- full prompts containing candidate data

---

## 33. MCP Strategy

MCPs are development-agent tools, not production requirements.

Kiro/Codex can use MCPs for:

- GitHub
- repository inspection
- docs lookup
- API documentation
- issues
- test workflows

ResumeMatch end users should **not** require MCP configuration.

---

## 34. GitHub / Task Workflow

Prefer issue-sized tasks.

Example:

```text
EPIC-01 Resume Processing

RM-001 Define upload constraints
RM-002 Implement PDF extraction
RM-003 Implement DOCX extraction
RM-004 Define StructuredResume
RM-005 Implement section parser
RM-006 Implement PII sanitizer
RM-007 Build parsed-profile review UI
```

Codex should normally receive one issue or a tightly related issue set, not:

> "Build ResumeMatch."

---

## 35. Requirements Style Kiro Should Use

Write implementation-ready requirements.

Use:

- **SHALL** = mandatory
- **SHOULD** = desired
- **MAY** = optional

Prefer:

> RM-PRIV-001: The backend SHALL NOT intentionally persist raw uploaded resume bytes after extraction.

over:

> ResumeMatch should have good privacy.

Each major requirement should include:

- ID
- requirement
- rationale where needed
- acceptance criteria
- dependencies
- priority
- milestone

---

## 36. Open Decisions Kiro Must Surface

Do not silently invent final answers.

At minimum flag:

1. Exact first role per domain.
2. Initial cloud LLM provider.
3. Exact PII categories.
4. Whether employer/university names leave the device.
5. First ATS/job source.
6. Deterministic vs LLM vs hybrid job-requirement extraction.
7. Initial scoring weights.
8. Strong Apply / Stretch / Skip thresholds.
9. Job caching strategy.
10. Browser state/storage approach.
11. Deployment platform.
12. Whether embeddings are needed at all in v1.
13. Rubric validation method.
14. Initial geography supported.
15. Finance sub-role taxonomy.
16. Hardware taxonomy:
   - embedded software
   - firmware
   - electronics
   - FPGA
   - verification
   - digital design

Kiro may propose defaults, but assumptions must be explicit.

---

## 37. Planning Files Kiro Should Produce

At minimum:

```text
requirements.md
architecture.md
AGENTS.md
```

Recommended:

```text
docs/
├── product-scope.md
├── user-flows.md
├── privacy-model.md
├── resume-schema.md
├── rubric-system.md
├── scoring-system.md
├── matching-system.md
├── job-ingestion.md
├── llm-provider-contract.md
├── security.md
├── testing-strategy.md
├── risks.md
├── roadmap.md
└── decisions/
```

If using Kiro Specs, a structure such as this is acceptable:

```text
.kiro/specs/resumematch/
├── requirements.md
├── design.md
└── tasks.md
```

Avoid contradictory duplicated sources of truth.

---

## 38. Definition of Done

A feature is not done merely because code exists.

A feature should generally require:

- requirement implemented
- acceptance criteria satisfied
- automated tests passing
- error states handled
- documentation updated
- privacy impact checked
- no unapproved scope expansion

Kiro should create global and feature-level definitions of done.

---

## 39. Expected End-State Experience

Eventually the user should see:

```text
YOUR JOB SEARCH

137 jobs analyzed

Strong Apply        21
Stretch             38
Skip                78
```

Opening a job:

```text
Company — Role

MATCH: 86%

Skills             91
Experience         82
Seniority          90
Domain             86

WHY YOU MATCH
✓ Evidence A
✓ Evidence B

GAPS
△ Skill X
△ Tool Y

APPLICATION STRATEGY
Apply: YES

Recommended truthful changes:
1. ...
2. ...
3. ...
```

And later:

```text
HIGHEST-ROI IMPROVEMENTS

1. SQL
   Requested by 54% of relevant jobs
   Estimated Opportunity Gain: High

2. Power BI
   Requested by 31%
   Estimated Opportunity Gain: Medium
```

---

# 40. Direct Instruction to Kiro

Using this handoff:

1. **Do not start implementation yet.**
2. Create the full planning/specification system first.
3. Turn ambiguous ideas into explicit assumptions or open decisions.
4. Keep requirements testable.
5. Preserve extensibility for five domains.
6. Keep the first implementation narrow.
7. Separate deterministic scoring from LLM explanation.
8. Treat privacy as a hard architecture boundary.
9. Treat role rubrics as configuration-driven contracts.
10. Treat job sources as adapters behind a common interface.
11. Design small implementation tasks suitable for Codex.
12. Define acceptance criteria before implementation.
13. Ensure generated planning files do not contradict each other.
14. Create milestone dependencies.
15. Flag risky assumptions that need prototypes before commitment.
16. Prevent scope creep.
17. Do not introduce technology merely because it is fashionable.
18. Make the simplest architecture that can support the stated product direction.

---

# 41. Immediate Output Requested From Kiro

Produce a planning package covering:

### Product
- product scope
- personas
- user journeys
- functional requirements
- non-functional requirements
- non-goals

### Engineering
- architecture
- module boundaries
- canonical schemas
- API contracts
- storage/session strategy
- privacy architecture
- security
- failure handling

### Intelligence Layer
- rubric contract
- readiness scoring
- job requirement extraction
- matching
- confidence/evidence model
- LLM responsibilities

### Delivery
- milestones
- task breakdown
- acceptance criteria
- testing strategy
- risk register
- steering/AGENTS rules

The result must be detailed enough that **Codex can implement ResumeMatch incrementally without redesigning the product while coding.**

---

# End of ResumeMatch Kiro Planning Handoff
