# AI-Powered Adaptive Exam Learning Platform
# Agent Operating Contract

This is the top-level operating contract for all AI coding agents working in this workspace. It governs the AI-Powered Adaptive Exam Learning Platform (FastAPI/Python backend and React/TypeScript frontend) as defined in `AI_Adaptive_Exam_Learning_Platform_PRD_SRS.md`.

All agent work is controlled by the WBS, stage-gated skills, an accepted-decision registry, explicit evidence, and documented state. Nothing is built on assumption alone — including technology choices.

---

## 1. Core Operating Principles

### 1.1 WBS-first execution

The WBS is the source of truth for **what gets built**.

Agents MUST:
- work from an active WBS leaf task;
- identify the WBS task ID before implementation;
- respect dependencies, scope, and acceptance criteria;
- update the WBS when scope or dependencies materially change;
- never silently expand a task into unrelated work.

If a request is larger than the current leaf task:
```text
STOP → identify scope expansion → update/revise WBS → select appropriate leaf task → resume lifecycle
```

### 1.2 Decision-first execution — the open technology list

The PRD (§27) intentionally leaves the following undecided, on purpose, for the architecture phase. **None of these may be chosen inline, silently, or differently between sessions.** An accepted ADR must exist in `docs/adr/` before any of the following is used, imported, or proposed in code:

- primary database technology
- Redis / caching strategy
- vector database technology
- background task framework
- message broker
- LLM provider(s) and the provider-abstraction layer
- embedding provider
- frontend framework
- object storage provider
- deployment platform
- authentication provider
- IRT / adaptive-testing implementation
- readiness-calibration methodology
- multimodal generation providers
- repository/service boundary (modular monolith vs. services)
- learning-state machine implementation (PRD §13)
- structured-output validation framework for LLM outputs (PRD FR-010)
- RAG chunking/embedding parameters (PRD FR-005, FR-008)

If no ADR exists for a decision the current task depends on:
```text
STOP → check docs/adr/ADR-INDEX.md → if PENDING: generate the ADR using docs/adr/ADR-PROMPT-TEMPLATE.md → present to user for acceptance → only then resume implementation
```

### 1.3 Non-negotiable product constraints

These are permanent, drawn directly from the PRD, and apply regardless of which WBS task is active. No design, WBS task, or Stage 2 artifact may propose violating one; if a task appears to require it, STOP and escalate.

1. LLM output must not directly become official learning state (§14.4, FR-001, FR-010).
2. Student state must be isolated per student and exam (§5.2, FR-022, NFR-002).
3. Learning-state transitions must be valid, application-enforced, and auditable (FR-001, §13, FR-025).
4. Generated questions must be validated before student use (FR-004, FR-015).
5. Source-grounded answers must use retrieval before generation (§14.3, FR-008).
6. Role-based access must be enforced server-side (FR-021, NFR-005).
7. Uploaded files must be treated as untrusted input (NFR-005, FR-005).
8. The system must not silently advance a student after a critical failure (NFR-004).
9. Important learning decisions must be explainable (NFR-008, FR-025).
10. Provider-specific logic must not be embedded in core learning logic (FR-023, NFR-007).

---

## 2. Evidence and Truthfulness

Agents MUST distinguish:
```text
VERIFIED
INFERRED
ASSUMED
UNKNOWN
BLOCKED
```

Rules:
- Never invent test or benchmark results.
- Never claim a fix without verification.
- Never claim a file/function/schema exists without inspecting the repository.
- Inspect complete logs before diagnosing runtime failures.
- When evidence is insufficient, explicitly state that it cannot be confirmed.

Prefer:
```text
Repository evidence + Executed commands/results + Relevant source implementation + Tests/benchmarks + Accepted ADRs
```
over intuition or memory of a different project.

---

## 3. Skill Inventory

| Stage / Skill | Directory | Purpose | Required Artifact |
|---|---|---|---|
| Stage 0: Roadmap & WBS Planner | `.agents/skills/roadmap-wbs-planner/` | Discovery, scope, epics, leaf tasks, dependencies | `roadmap_wbs.md` |
| Stage 1: Concept-to-Code Bridge | `.agents/skills/conceptual-understanding/` | Mental model, architecture, data flow, concept-to-code mapping | `task_X_Y_understanding.md` |
| Architecture / QA: Narrsistic Pluto | `.agents/skills/narrcisstic_pluto/` | Principal Architect & Lead QA/SRE analysis, 3–5 web-researched solutions, RCA, blast radius, rollout/rollback matrix | `task_X_Y_architect_analysis.md` |
| Stage 2: Codebase Design | `.agents/skills/codebase-design/` | Impact analysis, file-level design, blast radius, regression risk, rollback | `task_X_Y_design.md` |
| Stage 3: CS Domain Extraction | `.agents/skills/cs-domain-learning/` | First-principles CS/ML/security/infrastructure analysis | `task_X_Y_cs_concepts.md` |
| Stage 4: Testing & Verification | `.agents/skills/testing-verification/` | Test matrix, commands, verification, quality audit, completion | `task_X_Y_testing.md` |

Full skill files MUST be loaded only when that stage is being performed.

---

## 4. Mandatory Stage Lifecycle

```text
Stage 0: WBS
   ↓
Stage 1: Conceptual Understanding
   ↓
[Narrsistic Pluto: Multi-Pattern Architecture & QA/SRE Analysis] (when required)
   ↓
Stage 2: Codebase Design
   ↓
Stage 3: CS Domain Extraction (when required)
   ↓
Implementation
   ↓
Stage 4: Testing & Verification
   ↓
Completion
```

### 4.1 Triggering Narrsistic Pluto

The agent MUST load `.agents/skills/narrcisstic_pluto/` under the following conditions:
1. **Explicit User Triggers:** the user asks to "analyze this task like a principal architect," "give me 3–5 approaches with trade-offs," "do an RCA on this bug," or references "Narrsistic Pluto."
2. **Architectural Evaluation & Comparative Design:** choosing between competing patterns (sync vs. async task processing, caching strategy, RAG chunking strategy, mastery-model update strategy, schema-migration strategy) — Phase 3 of that skill MUST actively search the web for current idioms, library versions, and known caveats.
3. **Deep Defect Diagnostics & Incident RCA:** difficult bugs, regressions, or system failures requiring 5-Whys/Fishbone RCA.

Stage 3 (CS Domain Extraction) MUST be used for:
- adaptive-learning algorithms and mastery/IRT calculations;
- RAG retrieval and ranking behavior;
- misconception-graph reasoning;
- readiness modeling/calibration;
- embedding/vector search and model selection;
- LLM prompt/schema design and structured-output validation;
- architecture changes;
- unfamiliar runtime/framework behavior;
- difficult incidents whose root cause is not understood.

For simple, well-understood mechanical/configuration tasks, Stage 3 may be omitted.

The agent MUST NOT skip a necessary stage merely for speed.

---

## 5. Stage Gates

### Stage 0
Required: WBS task ID; objective; scope/out-of-scope; dependencies; acceptance criteria; learning objective; affected architectural domains (PRD §28); known risks. No implementation.

### Stage 1
Required: what; why; how; analogy where useful; architecture flow; data flow; cognitive-to-code mapping; relevant mathematics/framework/domain concepts; actual execution path when source inspection is required; verified vs. inferred behavior.

### Stage: Narrsistic Pluto (Principal Architect & QA/SRE Gate)
Required Artifact: `task_X_Y_architect_analysis.md`. Must include Phase 0 (task intake, assumptions ledger), Phase 1 (topology & semver/blast radius), Phase 2 (RCA, if a bug), Phase 3 (3–5 web-researched approaches with honest rejection reasons), Phase 4/4.5 (QA matrix, rollback triggers, ADR stub). Any technology conclusion from this stage still requires formal acceptance via `docs/adr/ADR-PROMPT-TEMPLATE.md` before it governs implementation.

### Stage 2
Required: current architecture; target architecture; `[NEW]`, `[MODIFY]`, `[DELETE]` files; call/data flow; dependency impact; blast radius; regression risk; rollback plan; test strategy. No code changes.

If implementation reveals a design defect:
```text
STOP → document discovery → re-enter Stage 2 → revise design → obtain required approval → resume
```

### Stage 3
When required, analyze: first principles → mathematics → generic mechanism → framework mechanism → project implementation → integration → failure modes/trade-offs.

### Stage 4
Required: environment checklist; exact test/build commands; complete relevant output; edge-case matrix; acceptance-criteria verification; regression verification; code-quality audit; completion report.

---

## 6. Implementation Rules

Implementation begins only after required stages and approvals.

Agents MUST:
- follow the approved Stage 2 design;
- remain inside WBS scope;
- preserve architectural-domain boundaries (PRD §28);
- isolate LLM/provider-specific behavior behind the LLM abstraction layer — never embed a provider SDK call directly in learning/domain logic (FR-023);
- add/update tests for behavior changes;
- avoid unrelated refactoring.

Agents MUST NOT:
- introduce infrastructure without WBS justification;
- introduce a dependency, library, or architectural pattern not covered by an accepted ADR or the approved Stage 2 design;
- modify unrelated systems;
- silently change API/architecture contracts;
- bypass verification;
- hide failures.

---

## 7. Error, Incident, and Failure Protocol

Errors are first-class engineering work. A runtime error, failing test, build failure, dependency failure, unexpected model behavior, integration failure, performance regression, or production incident MUST NOT automatically be handled with the smallest visible patch.

Required flow:
```text
ERROR / INCIDENT
      ↓
Capture complete evidence
      ↓
Classify problem
      ↓
Determine whether root cause is known
      ↓
Inspect relevant codebase deeply
      ↓
Trace execution / data / dependencies
      ↓
Determine root cause
      ↓
Assess blast radius / regression risk
      ↓
Apply relevant lifecycle stages
      ↓
Design fix → Implement → Targeted verification → Regression verification
      ↓
Update issue record → Update WBS if scope changed
      ↓
RESOLVE or remain OPEN/BLOCKED
```
A disappearing error is **not** automatically a resolved error.

### 7.1 Re-enter earlier stages when necessary

```text
Simple test typo: Stage 4 → fix → retest
Complex defect / systemic bug: Incident → Narrsistic Pluto (RCA) → Stage 2 → Stage 3 (if adaptive/AI logic involved) → Implementation → Stage 4
Unknown LLM/retrieval runtime failure: Stage 4 → Stage 1 → Stage 2 → Stage 3 → implementation → Stage 4
Architecture regression: Issue → Stage 1 → Narrsistic Pluto (if multiple recovery patterns needed) → Stage 2 → Stage 3 if required → fix → Stage 4
```

### 7.2 Root-cause requirements

For non-trivial failures, record: observed symptom; expected behavior; actual behavior; reproduction; first failing layer; execution path; relevant files/functions; relevant dependencies; verified root cause; contributing factors; affected scope; regression surface; fix; verification evidence.
These are not sufficient root causes: "It crashed." "The LLM failed." "Dependency issue." "Async problem." "Fixed by changing X." Those describe symptoms or patches, not mechanisms.

---

## 8. Issue and Error Register

The central register is `.agents/state/issues.md`. Every non-trivial error, failure, regression, incident, or unresolved technical issue MUST be recorded.

Template:
```markdown
## ISSUE-XXXX — Short title

Status: OPEN | INVESTIGATING | BLOCKED | FIXED_PENDING_VERIFICATION | RESOLVED | WONT_FIX
Severity: LOW | MEDIUM | HIGH | CRITICAL
Detected: YYYY-MM-DD
Detected During: WBS task / stage
Architectural Domain: (one of the PRD §28 domains, or "workspace")
Component: component/path
Symptom:
Reproduction:
Evidence:
Root Cause:
Contributing Factors:
Affected Scope:
Regression Risk: LOW | MEDIUM | HIGH
Related WBS:
Related Artifacts:
Fix:
Verification:
Regression Verification:
Resolution:
Remaining Risk:
Resolved On: YYYY-MM-DD
```

### Status rules
- `OPEN`: recorded, investigation not started.
- `INVESTIGATING`: active investigation.
- `BLOCKED`: cannot proceed because required information/access/environment/decision is unavailable.
- `FIXED_PENDING_VERIFICATION`: fix exists but original failure/regression is not fully verified.
- `RESOLVED`: original failure reproduced, fixed, verified, and relevant regression checks passed.
- `WONT_FIX`: intentionally not fixed with documented rationale.

Never mark an issue `RESOLVED` merely because code was edited.

---

## 9. Error-to-WBS Rules

An error can create new work. If resolution exceeds the current leaf scope:
```text
Issue discovered → root-cause analysis → scope assessment → create/update WBS task → implement under WBS control
```
The issue remains linked to the WBS task that resolves it. If the issue reveals an architectural flaw, update the WBS, relevant design artifacts, and — if it touches an item in §1.2 — the relevant ADR.

---

## 10. Regression Rules

Every non-trivial fix must consider: original failure + direct behavior + adjacent behavior + cross-domain integration + data compatibility + performance + security.

Platform request/response flow:
```text
Student / Admin Client
 ↓
API Layer (FastAPI, versioned)
 ↓
AuthN / AuthZ (RBAC, enforced server-side)
 ↓
Domain / Learning Orchestration
 ↓
Assessment Engine  |  Retrieval (RAG)  |  LLM Integration (behind abstraction)
 ↓
Persistence (Student State · Exam Config · Question Bank · Resources)
```

A local function passing while the learning-state contract breaks (e.g. an invalid stage transition, an unvalidated question reaching a student, or student data leaking across a template/exam boundary) is **NOT** a successful fix.

---

## 11. AI / Learning-Engine Verification Rules

Do not assume:
- LLM structured-output schema conformance;
- retrieval relevance/ranking behavior;
- mastery-threshold or readiness-calibration behavior;
- question-validation pass criteria;
- embedding model dimensions or distance metric;
- exam-template state-machine transition legality;
- background task/queue delivery guarantees;
- any behavior of a technology not yet covered by an accepted ADR.

For consequential engineering decisions, inspect the actual library/framework source and/or run an experiment. Production claims about model or pipeline behavior require reproducible evidence in the target environment, not assumption or memory of a different project's stack.

---

## 12. Repository Rules

Before moving, merging, copying, or deleting directories, determine: whether it is a git repository; its remote/origin; intended role among the PRD §28 architectural domains; whether it is source, dependency, experiment, or product code; whether other components depend on it.

These domains are conceptual and must **not** be split into separate services without an accepted ADR (§1.2) — the PRD explicitly warns against assuming a microservice split.
Do not infer repository ownership from directory names alone.

---

## 13. Progressive Disclosure

```text
Stage required → read that stage's SKILL.md → execute stage → produce artifact → continue lifecycle
```
Do not load every skill unnecessarily. When a task or failure requires multiple stages, activate all relevant skills.

---

## 14. Artifact and State Locations

Lifecycle artifacts: `.agents/artifacts/<epic-or-feature>/`

State:
```text
.agents/state/
├── current_task.md
├── current_stage.md
├── issues.md
└── decisions.md
```

Decision records: `docs/adr/`
```text
docs/adr/
├── ADR-PROMPT-TEMPLATE.md   ← use this to generate every ADR
├── ADR-INDEX.md             ← running index of pending + accepted decisions
└── ADR-NNN-<slug>.md        ← individual accepted/proposed decision records
```

`current_task.md` records the active WBS task, status, stage, dependencies, and blockers. `current_stage.md` records the active stage, required skill, status, artifact, and gate. `issues.md` is the central error/issue register. `decisions.md` is the durable, human-readable summary of **accepted** decisions only — full detail lives in `docs/adr/`.

---

## 15. User Approval Gates

Stop for user review after: Stage 0 WBS; Stage 2 Design; Stage 3 CS Learning (MUST STOP and present Stage 1–3 artifacts together; no implementation until explicit approval); Stage 4 Completion.

Additional approval is required for:
- architecture changes;
- security-policy changes;
- student-data lifecycle changes (retention, deletion, cross-exam sharing);
- LLM provider or model-routing policy changes;
- public API contract changes;
- material scope expansion;
- accepting unresolved HIGH/CRITICAL risk;
- accepting any new ADR under §1.2.

---

## 16. Completion Definition

A WBS leaf task is complete only when: acceptance criteria pass; required artifacts exist; required tests pass; relevant regression tests pass; implementation matches approved design; every open technology decision the task depended on has an accepted ADR; evidence is recorded; discovered issues are recorded with accurate status; WBS state is updated; required documentation is updated; no hidden blocker remains.

---

## 17. Agent Response Contract

At the end of each stage:
```text
WBS Task:
Current Stage:
Status:

Completed:
- ...

Evidence:
- ...

Artifacts:
- ...

Issues:
- ...

Decisions (accepted / pending):
- ...

Risks:
- ...

Next Required Stage:
...

User Approval Required:
YES / NO
```

After implementation:
```text
Implementation:
- Files changed
- Behavior changed

Verification:
- Commands
- Tests
- Results

Regression:
- Tests
- Results

Issues:
- ISSUE-XXXX
- Status

Final Status:
PASS / FAIL / BLOCKED
```

---

## 18. Golden Rules

**The agent does not decide what to build.** The WBS decides what to build.
**The agent does not silently decide architecture after approval.** The approved design decides how it is built.
**The agent does not decide open technology/library choices.** An accepted ADR in `docs/adr/` decides that — never inline, never silent, never differently between sessions. This is the rule that exists specifically to stop the drift this contract was written to fix.
**The agent does not decide whether implementation works.** Tests, logs, measurements, and evidence decide that.
**The agent does not merely patch errors.** Errors are investigated to root cause, their regression surface is assessed, and necessary lifecycle stages are applied.
**The agent may propose changes.** It must never silently change the project contract.
**The agent must inspect the actual PRD section and any accepted ADR before making an architecture claim** — never assume requirements from memory of a different project's stack, even one worked on in this same workspace.
**Agents must read all skills completely** and produce complete artifacts based on them — do not be lazy while creating those artifacts.
**The agent MUST STOP after Stage 3** and present Stage 1 (Understanding), Stage 2 (Design), and Stage 3 (CS Learning) artifacts to the user. No code or implementation changes are allowed until the user reads and explicitly approves.
**The agent MUST verify that any Pydantic/schema contract for LLM structured output matches the actual validation logic and downstream consumer 100%** — no partial or assumed schemas.

---

## 19. Terminal Command Error Lock & Mandatory Narrsistic Pluto RCA

- **Zero tolerance** for ANY terminal error (even small ones like lint warnings, test failures, build errors, or script misconfigurations).
- Agent must **IMMEDIATELY halt** all task work upon encountering an error.
- Must invoke the `narrsistic-pluto` skill for full Root Cause Analysis (RCA):
  - **Phase 0:** Task Intake & Assumptions Ledger
  - **Phase 1:** Blast Radius & Topology Check
  - **Phase 2:** Fault Activation Chain + 5-Whys/Fishbone RCA
  - **Phase 3:** Web-researched fix patterns (3-5 approaches)
  - **Phase 4:** QA Matrix & Rollback Triggers
- Must log the issue in `.agents/state/issues.md` as OPEN or INVESTIGATING.
- Must verify the fix explicitly and mark RESOLVED before resuming other work.
- A disappearing error is NOT automatically resolved. It must be explained.

---

## 20. Zero Silent Library & Dependency Ingestion Policy

- Agent is **STRICTLY FORBIDDEN** from defaulting to any library by training habit or assumption.
- Evaluation hierarchy:
  1. Check platform/language native capabilities first (e.g., `fetch` vs `axios`, `dataclasses` vs `pydantic`, `asyncio` vs `celery`).
  2. If third-party needed: evaluate 3-5 alternatives comparing bundle weight, type safety, CVE history, maintenance activity, and ecosystem longevity.
  3. Document trade-offs in the Stage 2 Design Artifact.
  4. Get explicit user approval before running any install command (`npm install`, `pip install`, etc.).
- Core architectural dependencies require a formal ADR in `docs/adr/`.
- Feature-level dependencies require Stage 2 sign-off.

---

## 21. Full-File Inspection & Zero Guesswork Protocol

- Before modifying any file: read the **ENTIRE file** from disk (all imports, class definitions, functions, exports).
- Before changing any function signature or return type: search and inspect **ALL callers** across the repository.
- No lazy placeholder snippets ("// ... rest unchanged").
- Evidence hierarchy: VERIFIED > INFERRED > UNVERIFIED (prohibited).
- No hallucinated file contents, test results, or API responses. Everything must be grounded in verified disk or terminal output.

---

## 22. Living Decision Architecture

- **4 Decision Registries:** ADR (Architecture), DDR (Data), AIDR (AI/LLM/RAG), FDR (Frontend).
- Decisions evolve during development, not pre-baked upfront.
- When a decision point surfaces: **HALT** → Narrsistic Pluto evaluation → Formal record → User acceptance.
- Supersession protocol: never silently override an accepted decision. If a change is needed, create a new record that supersedes the old one.

---

## 23. Two-Developer Team Protocol

- **Backend Track** (FastAPI/Python) and **Frontend Track** (React/TypeScript).
- Contract-First Development:
  - Backend designs API schemas in Stage 2.
  - Frontend generates TypeScript types from OpenAPI spec.
  - Frontend uses mock data/MSW until the backend endpoint is ready.
  - Zero blocking between tracks.
- Shared resources: `.agents/state/`, `docs/`, `.agents/rules/`.
- WBS tasks should be tagged `[BACKEND]` or `[FRONTEND]`.
- Decisions that affect both tracks require both developers' (agents') awareness and synchronization.

---

## 24. System Design Records (SDR) Protocol

- Maintained in `docs/system_design/` for domain logic, state machines, and algorithms.
- Created just-in-time when WBS tasks require them.
- Must include: What, Why, How it works, Mathematical formulas where applicable, Integration points, and Failure modes.

---

## 25. AI/LLM/RAG Decision Protocol

- Maintained in `docs/ai_design/` for prompt versioning, RAG pipeline architecture, LLM gateways, structured output validation, and agentic orchestration.
- Every AI component must have explicit evaluation criteria and benchmarks.
- Prompt changes require regression evaluation before deployment.

---

## 26. Automated Two-Developer Git Kickstart & Handover Protocol

Every AI agent operating in this workspace (Backend or Frontend track) MUST automatically execute this lifecycle around every WBS task:

### 26.1 Pre-Task Kickstart (Before Stage 1 / Implementation)
1. **Branch Hygiene:** Inspect Git status. Ensure work is rooted on the latest `main` branch (`git checkout main && git pull --rebase origin main`) before starting a new task card.
2. **Branch Creation:** Create and switch to the task-isolated feature branch following the naming standards in `docs/team/COLLABORATION-QUICKSTART.md` and Rule 06:
   - Backend track: `feat/be-task-X.Y-<slug>`
   - Frontend track: `feat/fe-task-A.B-<slug>`
3. **Track Isolation Enforcement:**
   - Backend agents are **STRICTLY FORBIDDEN** from modifying any files in `frontend/`.
   - Frontend agents are **STRICTLY FORBIDDEN** from modifying any files in `backend/`.

### 26.2 Post-Task Completion (After Stage 4 Verification)
1. **Selective Staging:** Stage ONLY track-specific files (`backend/` or `frontend/`), test files, and `.agents/state/` files. Never use blind `git add .`.
2. **Task-Based Conventional Commit:** Commit using format:
   ```text
   <type>(<scope>): [Task-X.Y] <imperative short summary>
   ```
3. **Push & Handover Command:** Provide copy-pasteable `git push -u origin <branch>` command for the developer.
4. **Contract-First Export:** If any backend endpoint or schema was modified, the backend agent MUST export `docs/contracts/schemas/openapi.json` to allow the frontend track to run `npm run typegen` with zero blocking.

---

## 27. Generic Developer Environment & Prerequisite Gating Protocol

Every AI agent operating in this repository MUST follow this universal prerequisite protocol before planning or executing any task:

### 27.1 Pre-Flight Environment & Credential Audit
Before entering Stage 1 or writing code for any task requiring external services (LLMs, databases, vector indices, storage buckets, message queues, OAuth):
1. **Inspect `.env` & Environment:** Check if the required environment variables are defined.
2. **Zero-Setup Guarantee:** If external services are not configured, verify if the task can run on zero-setup local defaults (e.g. SQLite, local Qdrant disk, in-memory cache, local mocks).
3. **Halt on Missing Required Credentials:** If a real external service or API key is strictly required for the task and missing from `.env`, the agent MUST NOT crash or hallucinate dummy data. It MUST halt and output the standardized **Developer Action Card**.

### 27.2 Universal Developer Action Card Standard
The agent must present this card directly to the developer:
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔑 DEVELOPER PREREQUISITE ACTION REQUIRED                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. WHAT IS NEEDED:        [Component name, e.g. LLM API / S3 Storage / DB]  │
│ 2. WHY IT IS NEEDED:      [Which WBS task / feature requires this]          │
│ 3. WHERE TO GET IT (URLs):                                                  │
│    • Free / Fastest Option: [Portal URL + 1-minute signup instructions]     │
│    • Aggregator / Multi:    [Portal URL, e.g. OpenRouter]                   │
│    • 100% Free / Offline:   [Download URL for local tool, e.g. Ollama]      │
│    • Standard / Enterprise: [Official vendor portal URL]                    │
│ 4. WHERE TO PUT IT:       [Exact file: .env]                                │
│    • Exact Variable Name:   KEY_NAME=your_value_here                        │
│ 5. ZERO-SETUP FALLBACK:   [Explain how to run with local mock if skipped]   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 27.3 Living `.env.example` Synchronization
Whenever any task introduces a new configuration parameter, secret, or third-party service:
- The agent MUST immediately update `.env.example` (both in root and `backend/`).
- Every entry MUST include a 1-line description, safe local default, and direct registration URL.
- Consult `docs/team/DEVELOPER_PREREQUISITES.md` as the definitive guide.
