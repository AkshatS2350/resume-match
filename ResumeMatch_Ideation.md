# ResumeMatch — Product Ideation & Pre-Requirements Document

> Working document for product discovery, architecture decisions, domain-rubric design, and future conversion into `requirements.md`.
>
> **Status:** Ideation / pre-spec
> **Primary goal:** Define what ResumeMatch should become before implementation begins.

---

# 1. Product Thesis

ResumeMatch should not be positioned as a generic "AI resume grader."

It should become a **privacy-first career and job-application decision engine** that helps a candidate answer five questions:

1. **How competitive is my current profile for a specific role?**
2. **Which jobs should I apply to, stretch for, or skip?**
3. **Why am I or am I not a fit?**
4. **What truthful changes would improve my application for this specific job?**
5. **Which skills, projects, certifications, or experiences would improve the largest number of future opportunities?**

The product combines:

- structured resume parsing,
- privacy-preserving preprocessing,
- domain-specific candidate evaluation,
- live job ingestion,
- explainable job matching,
- application guidance,
- evidence-backed gap analysis,
- optional local or cloud LLM reasoning.

The long-term value is not the resume score itself. The value is **decision support for the candidate's job search**.

---

# 2. Initial Validated Domains

The platform should initially support five broad domains:

1. **Software Engineering (SWE)**
2. **Finance**
3. **Embedded Systems / Hardware Engineering**
4. **Marketing**
5. **Supply Chain / Operations**

These should not be treated as five single rubrics. Each domain is a **rubric family** containing role-specific profiles.

Example:

```text
Finance
├── Financial Analyst
├── Investment Banking Analyst
├── Equity Research
├── Credit Analyst
├── Risk Analyst
├── Fund Accounting / Fund Servicing
└── FP&A
```

Likewise:

```text
Software Engineering
├── Backend
├── Frontend
├── Full Stack
├── Data Engineering
├── DevOps / Cloud
├── Mobile
└── Generalist / New Grad SWE
```

This avoids creating one misleading "Finance Score" or "SWE Score."

---

# 3. Why Multi-Domain Support Matters

The purpose of supporting several domains is not simply breadth.

It tests whether ResumeMatch's architecture can genuinely generalize across professions where hiring signals differ dramatically.

Examples:

| Signal | SWE | Finance | Embedded | Marketing | Supply Chain |
|---|---:|---:|---:|---:|---:|
| GitHub/projects | High | Low-Medium | High | Low | Low |
| Certifications | Low-Medium | Medium-High | Medium | Medium | Medium |
| Quantified business impact | Medium | High | Medium | Very High | Very High |
| Tools/software | High | High | Very High | High | High |
| Portfolio | Medium-High | Low-Medium | High | High | Low-Medium |
| Domain knowledge | Medium | Very High | Very High | High | Very High |
| Academic coursework | Medium | Medium | High for entry roles | Low-Medium | Medium |
| Internships | High | Very High | Very High | High | High |
| Keyword matching | Medium | Medium | Medium | Medium | Medium |
| Years/seniority | High | High | High | High | High |

A successful architecture should let these differences live in config and rules rather than hardcoded branching logic.

---

# 4. Product Principles

## 4.1 Privacy must be technically inspectable

Avoid vague promises such as:

> "Your resume never leaves your computer."

unless that is literally true for a particular mode.

Instead support explicit privacy modes.

### Mode A — Local Only

- File parsing occurs locally.
- Resume structuring occurs locally.
- PII removal occurs locally.
- LLM inference uses Ollama/local model.
- No resume-derived content leaves the device.

### Mode B — Sanitized Cloud

- Parsing and PII stripping happen before cloud inference.
- Only sanitized structured fields are transmitted.
- User can inspect the outbound payload.

### Mode C — Full Cloud (optional, future)

- Higher-quality model path.
- Explicit consent required.
- Clear disclosure before transmission.

The UI should clearly indicate which mode is active.

---

## 4.2 Scores should be explainable and mostly deterministic

An LLM should not arbitrarily decide that a resume is "74/100."

The system should separate:

```text
Evidence Extraction
       ↓
Deterministic / rule-based scoring
       ↓
LLM explanation and coaching
```

The LLM may help identify evidence, normalize descriptions, or interpret ambiguous statements, but the final rubric calculation should be reproducible wherever practical.

---

## 4.3 Evidence over unsupported advice

ResumeMatch should not tell users to acquire a skill merely because the LLM believes it is useful.

Instead:

```text
SQL appears in 68% of high-match Data Analyst jobs.
Your profile currently does not show SQL evidence.
Learning priority: HIGH.
```

Recommendations should ideally contain:

- evidence source,
- frequency or importance,
- affected jobs,
- expected benefit,
- confidence level.

---

## 4.4 Never encourage fabrication

ResumeMatch must distinguish between:

- rewriting existing truthful evidence,
- surfacing overlooked experience,
- recommending future learning,
- fabricating experience.

The product should never produce false claims such as:

> "Add AWS experience."

if AWS experience is not supported by the candidate profile.

Instead:

> "AWS appears frequently in otherwise suitable roles. Consider learning it or completing a project before claiming it on your resume."

---

## 4.5 Job matching must reflect employability, not keyword similarity

Skill overlap alone is insufficient.

A new graduate may match many technologies in a Senior Engineer job but still be an unrealistic candidate.

Matching therefore needs:

- skills,
- experience,
- seniority,
- education,
- domain fit,
- role similarity,
- required qualifications,
- preferred qualifications,
- geography,
- work authorization where relevant,
- remote/on-site preference,
- candidate constraints.

---

# 5. User Personas

## Persona A — New Graduate

Needs:

- "Which roles am I actually ready for?"
- project recommendations,
- missing skills,
- internship/new-grad job discovery,
- resume signal improvement.

## Persona B — Career Switcher

Needs:

- transferable skill detection,
- role feasibility,
- gap analysis,
- bridge-project recommendations,
- realistic target roles.

## Persona C — Early Career Professional

Needs:

- better targeting,
- resume tailoring,
- adjacent role discovery,
- salary/seniority progression signals later.

## Persona D — Privacy-Conscious Candidate

Needs:

- local inference,
- transparency,
- self-hosting,
- no persistent resume storage.

## Persona E — Open-Source Contributor / Domain Expert

Needs:

- rubric schema,
- testing framework,
- contribution documentation,
- versioning,
- validation datasets.

---

# 6. Core Product Flow

```text
Upload Resume
    ↓
Parse Document
    ↓
Generate Structured Candidate Profile
    ↓
PII Detection + Sanitization
    ↓
User Reviews Parsed Profile
    ↓
Select Target Domain / Role
    ↓
Answer Minimal Context Questions
    ↓
Candidate Rubric Evaluation
    ↓
Ingest / Retrieve Relevant Jobs
    ↓
Normalize Jobs
    ↓
Extract Job Requirements
    ↓
Candidate ↔ Job Matching
    ↓
Apply / Stretch / Skip Classification
    ↓
Application Guidance
    ↓
Skill / Experience Gap Aggregation
    ↓
Career Improvement Recommendations
```

The **profile review step** is important. Resume parsers will make mistakes; users should be able to correct extracted information before downstream scoring.

---

# 7. Structured Candidate Profile

The canonical profile should not be equivalent to raw resume text.

Possible model:

```yaml
candidate:
  summary:
    total_experience_months: 18
    career_stage: early_career

  skills:
    - name: Python
      category: programming_language
      evidence_count: 3
      evidence_strength: strong

  experience:
    - role_family: audit
      title_normalized: Audit Associate
      duration_months: 12
      industries:
        - financial_services
      evidence:
        - performed financial statement analysis
        - automated reconciliation workflow

  education:
    - degree_level: bachelors
      field: electronics_engineering
      graduation_year: 2027

  projects:
    - category: embedded_systems
      technologies:
        - ESP32
        - C++
      evidence_strength: medium

  certifications: []

  preferences:
    target_roles: []
    locations: []
    remote_preference: null
```

Each extracted field should ideally retain an internal pointer to its source evidence.

Example:

```yaml
skill:
  name: SQL
  evidence:
    source_section: project_2
    source_text_hash: ...
```

This enables explainability.

---

# 8. Job Schema

All external job sources should normalize into one schema.

```yaml
job:
  source: greenhouse
  external_id: ...
  company: ...
  title_raw: ...
  title_normalized: ...
  role_family: ...
  seniority: entry
  location:
    city: ...
    country: ...
    remote_type: hybrid

  employment_type: full_time

  experience:
    min_years: 0
    max_years: 2

  required_skills: []
  preferred_skills: []
  required_education: []
  preferred_education: []
  certifications: []

  responsibilities: []
  domain_signals: []

  posted_at: ...
  application_url: ...
```

Raw descriptions should be retained separately from normalized fields where legally and technically appropriate.

---

# 9. Domain Rubric Architecture

A rubric should be configuration-driven.

Suggested hierarchy:

```text
Domain
  ↓
Role Family
  ↓
Role Profile
  ↓
Seniority Profile
```

Example:

```text
Embedded Systems
  → Firmware Engineering
      → Entry Level
      → Mid Level
```

Possible config:

```yaml
domain: embedded_systems
role: firmware_engineer
seniority: entry

categories:
  programming:
    weight: 20
    signals:
      - c
      - cpp
      - embedded_c

  microcontrollers:
    weight: 20

  protocols:
    weight: 15

  debugging:
    weight: 15

  projects:
    weight: 15

  electronics_fundamentals:
    weight: 10

  communication:
    weight: 5
```

Rubrics should support:

- weighted signals,
- required signals,
- bonus signals,
- mutually substitutable signals,
- seniority-dependent weights,
- confidence values,
- evidence thresholds.

---

# 10. Initial Domain Ideation

## 10.1 Software Engineering

Possible role families:

- New Grad / General SWE
- Backend
- Frontend
- Full Stack
- Data Engineering
- DevOps / Cloud
- Mobile
- QA / Automation

Possible scoring dimensions:

- programming languages,
- algorithms / problem solving,
- frameworks,
- databases,
- APIs,
- cloud,
- testing,
- version control,
- project depth,
- production deployment,
- internships / professional experience,
- system design for relevant seniority,
- measurable impact,
- CS fundamentals.

Important nuance:

A college project should not receive the same evidence strength as equivalent production experience.

---

## 10.2 Finance

Possible role families:

- Financial Analyst
- FP&A
- Equity Research
- Credit Analysis
- Risk
- Fund Servicing / Middle Office
- Investment Banking Analyst
- Corporate Finance

Possible dimensions:

- accounting,
- financial statement analysis,
- valuation,
- financial modelling,
- Excel,
- market knowledge,
- industry knowledge,
- audit / transaction exposure,
- portfolio / investment analysis,
- certifications,
- data skills,
- presentation / writing,
- regulatory/domain knowledge,
- reconciliation/control experience for operations roles.

Role differences matter heavily.

For example, CFA progress may matter more for equity research than for fund operations, while reconciliations and NAV exposure may matter heavily for fund servicing.

---

## 10.3 Embedded Systems / Hardware

Possible role families:

- Firmware Engineer
- Embedded Software Engineer
- Hardware Design Engineer
- Validation / Verification Engineer
- FPGA Engineer
- IoT Engineer
- PCB / Electronics Engineer

Potential dimensions:

- C / C++,
- microcontrollers,
- embedded Linux,
- RTOS,
- device drivers,
- communication protocols,
- electronics fundamentals,
- digital logic,
- computer architecture,
- debugging tools,
- oscilloscope / logic analyzer exposure,
- PCB design,
- FPGA / Verilog / VHDL,
- sensors / peripherals,
- hardware-software integration,
- project depth,
- testing / validation,
- datasheet reading.

Potential domain-specific insight:

A strong GitHub repository alone may not prove hardware competence. Evidence could include:

- schematics,
- PCB files,
- test logs,
- firmware,
- measurements,
- demo videos,
- design tradeoffs.

ResumeMatch could eventually recognize project-evidence quality.

---

## 10.4 Marketing

Possible role families:

- Digital Marketing
- Performance Marketing
- Brand Marketing
- Product Marketing
- Content Marketing
- Growth Marketing
- Marketing Analytics

Potential dimensions:

- campaign ownership,
- measurable ROI,
- CAC / CPL / conversion metrics,
- SEO / SEM,
- paid media,
- analytics,
- CRM,
- content strategy,
- market research,
- positioning,
- experimentation,
- attribution,
- tools/platforms,
- portfolio/campaign evidence,
- stakeholder communication.

Marketing rubrics should heavily reward quantified impact.

Example:

```text
Weak evidence:
"Managed social media campaigns."

Strong evidence:
"Reduced campaign CAC by 18% while increasing qualified leads by 31%."
```

---

## 10.5 Supply Chain / Operations

Possible role families:

- Supply Chain Analyst
- Operations Analyst
- Procurement Analyst
- Logistics Analyst
- Demand Planner
- Inventory Analyst
- Manufacturing Operations

Potential dimensions:

- Excel,
- SQL / analytics,
- ERP tools,
- SAP / Oracle,
- forecasting,
- inventory management,
- procurement,
- logistics,
- process improvement,
- Lean / Six Sigma,
- KPI ownership,
- supplier management,
- optimization,
- cost reduction,
- planning,
- operations research,
- reporting / dashboards.

Impact evidence should include metrics such as:

- inventory reduction,
- service level,
- on-time delivery,
- lead time,
- forecast accuracy,
- fill rate,
- procurement savings,
- throughput,
- defect rate.

---

# 11. Evidence Strength Model

Signals should have evidence strength.

Example levels:

```text
0 — Not present
1 — Claimed only
2 — Coursework / certification
3 — Personal project
4 — Internship / supervised practical use
5 — Professional ownership / measurable impact
```

This avoids treating:

> "Python"

in a skill section the same as:

> "Built and deployed a Python service processing 2M events/day."

Possible internal representation:

```yaml
signal:
  name: python
  level: 4
  confidence: 0.91
  sources:
    - work_experience_1
    - project_2
```

---

# 12. Candidate Readiness vs Job Match

These should be separate metrics.

## Candidate Readiness Score

Measures readiness for a role family independent of one specific vacancy.

Example:

```text
Firmware Engineer Readiness: 72/100
```

## Job Match Score

Measures fit against a particular posting.

Example:

```text
NVIDIA Firmware Intern: 81/100
```

A candidate could have:

```text
Role readiness: 62
Specific job match: 84
```

if a particular job aligns unusually well with their background.

---

# 13. Proposed Job Match Model

Initial conceptual model:

```text
Job Match Score =
  Skills Match
+ Experience Match
+ Seniority Match
+ Domain Match
+ Education Match
+ Tool/Technology Match
+ Location / Work Constraints
+ Evidence Strength
- Hard Requirement Penalties
```

Suggested classification:

### Strong Apply
Candidate satisfies most critical requirements and has credible evidence.

### Apply
Good enough fit; normal gaps exist.

### Stretch
Meaningful gaps, but application is not unreasonable.

### Skip
Hard constraints or major seniority/domain mismatch.

The classification thresholds should be configurable and validated empirically.

---

# 14. Hard Requirements vs Preferences

A common ATS mistake is treating every JD phrase equally.

ResumeMatch should distinguish:

```text
REQUIRED
- legally mandatory credential
- work authorization
- minimum years when clearly strict
- core technology

PREFERRED
- nice-to-have technologies
- certifications
- domain familiarity

CONTEXTUAL
- generic teamwork statements
- boilerplate values
```

This could be partly rule-driven and partly LLM-extracted.

---

# 15. Skill Ontology / Normalization

A major hidden requirement is taxonomy.

Examples:

```text
C++ == CPP == C Plus Plus
MS Excel == Microsoft Excel == Excel
Meta Ads == Facebook Ads
SAP S/4HANA belongs to SAP / ERP
STM32 belongs to MCU / ARM Cortex ecosystem
```

The system needs a canonical ontology.

Possible structure:

```yaml
skill:
  id: cpp
  display_name: C++
  aliases:
    - cpp
    - c plus plus
  categories:
    - programming_language
  domains:
    - software_engineering
    - embedded_systems
```

Long-term, this ontology becomes one of the project's most valuable assets.

---

# 16. Job Ingestion Architecture

Avoid scraping LinkedIn or Indeed.

Possible sources:

- Greenhouse
- Lever
- Ashby
- Adzuna
- USAJobs
- additional compliant APIs later

Architecture:

```text
ATS Connectors
      ↓
Raw Job Records
      ↓
Normalizer
      ↓
Deduplicator
      ↓
Requirement Extractor
      ↓
Canonical Job Store / Search Index
```

A **company registry** may be required for ATS APIs that expose jobs per organization.

Example:

```yaml
company:
  name: Example Corp
  ats: greenhouse
  board_id: examplecorp
```

Future community contribution idea:

```text
companies.yaml
```

where contributors add public ATS endpoints.

---

# 17. Storage Philosophy

The product should distinguish between different data classes.

## Never persist by default

- original resume bytes,
- raw PII,
- cloud-bound unsanitized profile.

## User-controlled local/session state

- structured profile,
- selected roles,
- analysis results.

## Safe server-side persistence may eventually include

- public job postings,
- rubric configs,
- skill ontology,
- anonymous system metrics,
- company registry.

Privacy marketing should refer specifically to **candidate data**, not claim the whole application has no database.

---

# 18. PII Strategy

Potential PII classes:

- name,
- email,
- phone,
- street address,
- personal links,
- usernames,
- candidate IDs,
- references,
- identifiable project/customer names where necessary.

Possible pipeline:

```text
Regex rules
   +
PII detection library
   +
Named-entity detection
   +
User preview
   ↓
Sanitized payload
```

Important design rule:

**PII removal is a safety layer, not a perfect anonymity guarantee.**

A highly unique career history may still identify an individual.

The product documentation should be transparent about that.

---

# 19. LLM Provider Architecture

Provider interface could be more granular than only `grade()` and `match()`.

Suggested interface:

```python
class LLMProvider:
    def extract_resume_structure(...): ...
    def extract_job_requirements(...): ...
    def explain_score(...): ...
    def generate_application_guidance(...): ...
    def summarize_skill_gaps(...): ...
```

The deterministic engine should own actual scoring.

Providers might include:

```text
GeminiProvider
OllamaProvider
OpenAIProvider        # future contributor
ClaudeProvider        # future contributor
```

Local models may be used only for supported subtasks if their quality is insufficient elsewhere.

---

# 20. Application Coach

For each job, output could include:

### Fit Summary

```text
Match: 82%
Recommendation: APPLY
Confidence: High
```

### Why You Match

- three to five strongest evidence-backed matches.

### Missing / Weak Signals

Separate:

- missing required,
- missing preferred,
- weakly evidenced,
- irrelevant/noise.

### Resume Changes

Only truthful modifications:

- reorder bullets,
- quantify existing work where data exists,
- emphasize relevant projects,
- replace vague wording,
- move relevant skills upward.

### Application Angle

Example:

> Position yourself as an audit professional moving toward fund operations, emphasizing reconciliations, controls, financial statements, and stakeholder coordination.

### Interview Preparation

Potential future module:

- likely topics,
- questions derived from JD,
- resume-specific vulnerability questions.

---

# 21. Career Gap Aggregator

This could become ResumeMatch's signature feature.

Rather than analyzing one job only:

```text
Candidate → 100 relevant jobs
```

Aggregate missing signals.

Example:

```text
Your Top Opportunity Gaps

SQL
Missing in profile
Required/preferred by 47 of top 70 jobs
Potential opportunity gain: +19 jobs
Priority: HIGH

Power BI
Appears in 28 jobs
Potential opportunity gain: +8 jobs
Priority: MEDIUM
```

Possible recommendation classes:

- Learn skill
- Build project
- Gain certification
- Improve resume evidence
- Target adjacent role instead
- Gain internship/work exposure

This changes ResumeMatch from a resume tool into a **career planning engine**.

---

# 22. Opportunity Gain Metric

Potential experimental metric:

```text
Opportunity Gain(skill) =
number of otherwise-viable jobs whose classification improves
if the candidate credibly acquires that skill
```

Example:

```text
Current:
Strong Apply: 14
Apply:        22
Stretch:      31
Skip:         73

If SQL evidence reaches level 3:
Strong Apply: 21
Apply:        28
Stretch:      24
Skip:         67
```

This could power:

> "What should I learn next?"

with actual job-market evidence.

---

# 23. Confidence System

The system should show confidence rather than fake certainty.

Example:

```text
Match Score: 78%
Confidence: Medium
```

Confidence may depend on:

- parsing quality,
- completeness of job description,
- ambiguous years of experience,
- evidence strength,
- role-classification certainty,
- LLM extraction agreement,
- missing candidate context.

---

# 24. Human-in-the-Loop Corrections

Before grading:

```text
We extracted:

Experience: 1 year 4 months
Skills: Python, SQL, Excel, C++
Target: Data Analyst

[Edit profile]
[Continue]
```

The user should be able to correct:

- skill extraction,
- dates,
- project categories,
- role titles,
- target domain,
- experience level.

This will substantially improve reliability.

---

# 25. Potential UI Information Architecture

## Screen 1 — Upload

- Upload PDF/DOCX
- Privacy mode selector
- "What happens to my resume?"

## Screen 2 — Parsed Profile

- Experience
- Education
- Skills
- Projects
- Certifications
- edit controls

## Screen 3 — Target Role

```text
Domain: Embedded Systems
Role: Firmware Engineer
Level: Internship / Entry
```

## Screen 4 — Readiness

```text
Firmware Readiness: 71

Strong:
C/C++
Microcontrollers
Projects

Weak:
RTOS
Debugging evidence
Embedded Linux
```

## Screen 5 — Job Matches

Filters:

- Strong Apply
- Apply
- Stretch
- Skip
- location
- remote
- date posted
- experience

## Screen 6 — Job Detail

- Match explanation
- hard requirements
- skill gaps
- tailored resume advice
- application link

## Screen 7 — Career Insights

- top recurring gaps
- highest-ROI skills
- role alternatives
- recommended project themes

---

# 26. Domain Expert Validation

Community rubrics are valuable only if their quality is controlled.

Potential rubric lifecycle:

```text
Draft
  ↓
Community Review
  ↓
Domain Expert Reviewed
  ↓
Validated Against Job Dataset
  ↓
Stable
```

Rubric metadata:

```yaml
version: 1.2
status: reviewed
reviewers: 3
jobs_sampled: 500
last_updated: 2026-08
```

Eventually ResumeMatch could compare rubric expectations against real job-posting frequency.

---

# 27. Rubric Validation Dataset

For each role:

collect a representative sample of public jobs and derive:

- common required skills,
- common preferred skills,
- years of experience distribution,
- education frequency,
- certifications,
- technology frequency,
- recurring responsibility themes.

Rubrics should then combine:

```text
Domain Expert Judgment
+
Observed Job Market Data
```

rather than depending on either one alone.

---

# 28. Testing Strategy

## Resume parser tests

Use synthetic or consented resumes representing:

- one-column,
- two-column,
- tables,
- graphics-heavy,
- multi-page,
- unusual headings,
- ATS-friendly,
- poorly encoded PDFs.

## PII tests

Test:

- emails,
- phone variants,
- international numbers,
- addresses,
- LinkedIn/GitHub URLs,
- names,
- usernames,
- unusual contact blocks.

## Rubric tests

Known profile fixtures:

```text
Strong firmware candidate → expected high range
Marketing profile → expected low firmware range
Senior profile against internship → detect mismatch
```

## Matching tests

Test edge cases:

- perfect skills / wrong seniority,
- correct seniority / missing core requirement,
- transferable skills,
- empty job description,
- contradictory JD language.

## LLM regression tests

Structured outputs must satisfy schemas.

Never rely solely on exact string equality.

---

# 29. Evaluation Metrics

Potential internal metrics:

### Parsing

- field extraction precision,
- field extraction recall,
- date accuracy,
- section detection accuracy.

### PII

- PII recall is especially important,
- false negatives should be heavily penalized.

### Role Classification

- top-1 role-family accuracy,
- top-3 accuracy.

### Job Matching

Harder to validate.

Possible strategies:

- recruiter/domain-expert ranking comparisons,
- pairwise preference tests,
- candidate feedback,
- application/outcome data only if users explicitly opt in later.

### Recommendation Quality

Evaluate:

- factual grounding,
- evidence traceability,
- usefulness,
- hallucination rate,
- fabrication encouragement rate (target: zero).

---

# 30. MVP vs Full Vision

Supporting five domains does **not** mean every feature should be fully implemented for all five on day one.

Use a layered rollout.

## Prototype 0 — Architecture Proof

Domains:

- one role from SWE,
- one role from Finance,
- one role from Embedded,
- one role from Marketing,
- one role from Supply Chain.

Example:

```text
Backend Engineer
Financial Analyst
Firmware Engineer
Performance Marketing Analyst
Supply Chain Analyst
```

Purpose:

Validate that the rubric architecture generalizes.

Features:

- upload,
- parse,
- structured profile,
- select role,
- rubric score,
- explanations.

No large-scale job search required yet.

---

## MVP 1 — Job Matching

Add:

- ATS connectors,
- normalized jobs,
- role classification,
- match score,
- Apply / Stretch / Skip.

---

## MVP 2 — Application Coach

Add:

- per-job gap analysis,
- bullet improvements,
- application angle,
- privacy inspector.

---

## MVP 3 — Career Intelligence

Add:

- aggregate skill gaps,
- opportunity gain,
- learning priorities,
- adjacent role recommendations.

---

## Public v1

Expand role coverage within all five domains and stabilize:

- contributor framework,
- Docker/self-hosting,
- Ollama,
- provider abstraction,
- documentation,
- tests,
- rubric versioning.

---

# 31. Recommended First Role Profiles

To prove cross-domain flexibility, choose one representative role per domain.

## SWE

**Backend Engineer — Intern / New Grad**

Why:

- clear technical signals,
- project evidence matters,
- easy to test job matching.

## Finance

**Financial Analyst — Entry Level**

Why:

- broadly recognizable,
- combines accounting, Excel, modelling, and analytical signals.

Alternative if optimizing for more specialized differentiation:

**Fund Servicing / Operations Analyst.**

## Embedded

**Firmware / Embedded Software Engineer — Intern / Entry**

Why:

- distinct from generic SWE,
- rich technical rubric,
- demonstrates domain-aware architecture.

## Marketing

**Performance / Growth Marketing Analyst — Entry**

Why:

- metrics are highly measurable,
- tooling and impact can be scored.

## Supply Chain

**Supply Chain Analyst — Entry**

Why:

- quantitative,
- tool-based,
- domain-specific,
- clear operational KPIs.

---

# 32. Suggested Repository Structure

```text
resumematch/
│
├── apps/
│   ├── web/
│   └── api/
│
├── packages/
│   ├── resume_parser/
│   ├── pii/
│   ├── ontology/
│   ├── rubric_engine/
│   ├── job_matching/
│   ├── job_normalizer/
│   └── llm/
│
├── rubrics/
│   ├── software_engineering/
│   ├── finance/
│   ├── embedded_systems/
│   ├── marketing/
│   └── supply_chain/
│
├── connectors/
│   ├── greenhouse/
│   ├── lever/
│   ├── ashby/
│   └── adzuna/
│
├── ontology/
│   ├── skills.yaml
│   ├── roles.yaml
│   └── industries.yaml
│
├── fixtures/
│   ├── resumes/
│   └── jobs/
│
├── tests/
│
├── docs/
│   ├── architecture.md
│   ├── privacy.md
│   ├── rubric-authoring.md
│   └── contributing.md
│
└── docker/
```

Exact monorepo structure can change later; the important principle is separating rubric/domain data from core logic.

---

# 33. Technology Direction

Potential starting architecture:

## Frontend

- React + TypeScript
- lightweight component system
- browser-side parsing where feasible

## Backend

- FastAPI
- Pydantic schemas
- stateless candidate-analysis endpoints

Python is especially attractive because of:

- document parsing ecosystem,
- NLP ecosystem,
- Presidio/spaCy integration,
- ML experimentation,
- data-analysis tooling.

## Data

Candidate data:

- no persistent server-side database by default.

Job data:

- PostgreSQL or search index eventually makes sense.

Ephemeral state:

- memory/session token initially,
- Redis only if required.

## Local inference

- Ollama adapter.

## Cloud inference

Start with one provider only.

Provider abstraction exists from the beginning, but avoid implementing five providers before core quality is proven.

---

# 34. Questions the Future `requirements.md` Must Resolve

These are intentionally left open during ideation.

## Product

1. Is the primary unit of analysis a **role**, **job**, or both?
2. Does ResumeMatch require a target role before showing any results?
3. Should users be able to compare multiple career paths simultaneously?
4. Should application coaching rewrite complete resume sections or only suggest changes?

## Privacy

5. Which parsing steps must happen client-side?
6. Is sanitized cloud mode permitted to transmit employer/project names?
7. What exact candidate data can be cached?
8. How long may ephemeral state exist?

## Rubrics

9. What is the exact schema?
10. Which scoring categories are universal?
11. Which categories are role-specific?
12. How are evidence strength and confidence combined?
13. How are rubrics versioned?

## Jobs

14. Which source is implemented first?
15. Do we persist public job data?
16. How do we discover ATS company boards?
17. How is duplicate posting detection handled?
18. How old can a job be before it is hidden?

## Matching

19. What are the initial match-score weights?
20. Which requirements cause hard rejection?
21. How is seniority inferred?
22. How is transferable experience valued?
23. How should "preferred" requirements affect scores?

## LLM

24. Which tasks truly need an LLM?
25. Which tasks should be deterministic?
26. Which structured-output schemas are mandatory?
27. What happens when local-model output quality is poor?

## UX

28. How much manual profile correction is expected?
29. How are score explanations visualized?
30. How do users inspect privacy payloads?
31. How should uncertainty be displayed?

## Open Source

32. Can contributors add rubrics without code changes?
33. How are rubric PRs validated?
34. Can third-party job connectors be plugins?
35. Is the skill ontology community editable?

---

# 35. Anti-Goals for Initial Versions

Explicitly avoid initially:

- automatic job applications,
- LinkedIn scraping,
- recruiter outreach automation,
- cover-letter spam generation,
- salary prediction,
- offer probability claims,
- personality testing,
- psychometric hiring predictions,
- storing full candidate histories/accounts,
- dozens of domains,
- fine-tuning custom LLMs,
- browser extensions,
- mobile apps,
- enterprise ATS integration.

These distract from proving the core engine.

---

# 36. Major Risks

## Risk 1 — False precision

A score like `82.4%` may imply scientific certainty.

Mitigation:

- use ranges or rounded scores,
- show confidence,
- explain evidence.

## Risk 2 — Rubric bias

Hiring practices are neither universal nor perfectly objective.

Mitigation:

- source rubrics from job-market data + experts,
- version them,
- expose criteria,
- allow multiple role profiles.

## Risk 3 — LLM hallucinations

Mitigation:

- JSON schemas,
- evidence references,
- deterministic scoring,
- no unsupported resume claims.

## Risk 4 — Parser unreliability

Mitigation:

- profile review,
- multiple extraction strategies,
- fixtures and regression tests.

## Risk 5 — Job coverage

Mitigation:

- transparent source coverage,
- company registry,
- multiple compliant connectors.

## Risk 6 — Scope explosion

Mitigation:

- one initial role per domain,
- shared engine first,
- deeper role coverage later.

---

# 37. What Would Make This Project Genuinely Impressive

ResumeMatch becomes significantly stronger if it can demonstrate these claims with working engineering:

1. **One engine supports five professionally different domains without hardcoded domain branching.**
2. **Scores are explainable and reproducible.**
3. **Every recommendation points back to resume or job evidence.**
4. **Candidate data can remain local or sanitized before cloud processing.**
5. **Live jobs from multiple ATS sources normalize into one schema.**
6. **Matching understands seniority and hard constraints rather than keywords only.**
7. **The system can identify which missing skill unlocks the most realistic opportunities.**
8. **Community members can add role rubrics through configuration rather than modifying the scoring engine.**

That combination moves the project beyond an LLM demo and into a credible open-source career intelligence system.

---

# 38. Proposed Product North Star

The ideal user experience is not:

> "Your resume scored 72/100."

It is:

```text
Based on your current profile:

Strong Apply     18 jobs
Apply            31 jobs
Stretch          24 jobs
Skip             67 jobs

Your highest-value gap is SQL.
Adding credible SQL project/work evidence would likely improve your fit for 17 currently borderline roles.

Your strongest target roles are:
1. Operations Analyst
2. Financial Analyst
3. Risk Analyst

For this specific JPMorgan role:
Recommendation: APPLY
Reason: strong accounting/control overlap; moderate SQL gap; correct seniority.
```

That is the product ResumeMatch should ultimately aim to become.

---

# 39. Recommended Build Sequence

```text
PHASE 0
Define schemas
↓
Skill ontology
↓
Rubric format
↓
Five reference role rubrics

PHASE 1
Resume extraction
↓
Structured profile
↓
PII stripping
↓
Profile correction UI

PHASE 2
Deterministic readiness engine
↓
Evidence strength
↓
LLM explanations

PHASE 3
One ATS connector
↓
Job normalization
↓
Requirement extraction
↓
Matching engine

PHASE 4
More job connectors
↓
Apply/Stretch/Skip
↓
Application coach

PHASE 5
Aggregate job-market gaps
↓
Opportunity Gain
↓
Career intelligence

PHASE 6
Ollama
↓
Self-hosting
↓
Community rubrics
↓
Public open-source release
```

---

# 40. Next Document

The next artifact should be:

```text
requirements.md
```

It should convert this ideation document into testable statements covering:

- functional requirements,
- non-functional requirements,
- schemas,
- privacy guarantees,
- MVP boundaries,
- APIs,
- domain/rubric requirements,
- job-ingestion requirements,
- matching requirements,
- acceptance criteria,
- testing requirements,
- phased milestones.

Before that file is frozen, the most important design decisions to settle are:

1. canonical candidate schema,
2. canonical job schema,
3. rubric schema,
4. evidence-strength model,
5. match-score model,
6. initial five reference roles,
7. privacy modes,
8. first ATS connector,
9. exact MVP boundary.

---

## Current Recommended Reference Roles

| Domain | Initial Reference Role |
|---|---|
| Software Engineering | Backend Engineer — Intern / New Grad |
| Finance | Financial Analyst — Entry Level |
| Embedded / Hardware | Firmware Engineer — Intern / Entry |
| Marketing | Performance Marketing Analyst — Entry |
| Supply Chain / Operations | Supply Chain Analyst — Entry |

These five roles should be used to test whether the underlying architecture genuinely generalizes before expanding each domain into many sub-roles.
