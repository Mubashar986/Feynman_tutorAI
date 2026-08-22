# ADR Index — AI Adaptive Exam Learning Platform

Status legend: `PENDING` (not started) · `IN_PROGRESS` · `PROPOSED` (generated, awaiting user acceptance) · `ACCEPTED` · `SUPERSEDED`

No implementation may depend on a `PENDING` or `IN_PROGRESS` row below.
Generate each using [ADR-PROMPT-TEMPLATE.md](./ADR-PROMPT-TEMPLATE.md) in this folder. Once a decision is `ACCEPTED`, add its summary to `.agents/state/decisions.md` and create `ADR-NNN-<slug>.md` here with the full record.

## Scope decision (resolve first — everything else is easier once this exists)

| ID | Decision | PRD Reference | Status | Record File |
|---|---|---|---|---|
| **ADR-000** | MVP capability slice — 3-Phase Milestone delivery boundary | §1, §3.1 | **ACCEPTED** | [ADR-000-mvp-capability-slice.md](./ADR-000-mvp-capability-slice.md) |

## Foundational technology decisions (PRD §27 — explicitly left open)

| ID | Decision | PRD Reference | Status | Record File |
|---|---|---|---|---|
| **ADR-001** | Primary database technology (PostgreSQL + SQLModel / SQLite dev) | §27 | **ACCEPTED** | [ADR-001-primary-database.md](./ADR-001-primary-database.md) |
| **ADR-002** | Redis usage / caching strategy | §27 | **ACCEPTED** | [ADR-002-caching-strategy.md](./ADR-002-caching-strategy.md) |
| **ADR-003** | Vector database technology (Qdrant local disk / remote) | §27 | **ACCEPTED** | [ADR-003-vector-database.md](./ADR-003-vector-database.md) |
| **ADR-004** | Background task framework (ARQ on Redis) | §27, §19 | **ACCEPTED** | [ADR-004-background-tasks-and-broker.md](./ADR-004-background-tasks-and-broker.md) |
| **ADR-005** | Message broker (Redis broker for ARQ) | §27, §19 | **ACCEPTED** | [ADR-004-background-tasks-and-broker.md](./ADR-004-background-tasks-and-broker.md) |
| **ADR-006** | LLM provider selection + abstraction layer (Multi-Provider Gateway) | §27, FR-023 | **ACCEPTED** | [ADR-006-llm-provider-abstraction.md](./ADR-006-llm-provider-abstraction.md) |
| **ADR-007** | Embedding provider (Gateway with FastEmbed / Gemini / OpenAI) | §27, FR-008 | **ACCEPTED** | [ADR-006-llm-provider-abstraction.md](./ADR-006-llm-provider-abstraction.md) |
| **ADR-008** | Frontend framework (React 18+ / Vite / TS / Tailwind / Shadcn UI) | §27, §17 | **ACCEPTED** | [ADR-008-frontend-framework-and-ui-stack.md](./ADR-008-frontend-framework-and-ui-stack.md) |
| ADR-009 | Object storage provider (Local / S3 / MinIO) | §27 | PENDING | To be resolved in Epic 3 |
| ADR-010 | Deployment platform | §27 | PENDING | To be resolved in Epic 0.2 |
| **ADR-011** | Authentication provider (FastAPI OAuth2 Bearer + PyJWT + bcrypt) | §27, FR-021 | **ACCEPTED** | [ADR-011-auth-and-rbac.md](./ADR-011-auth-and-rbac.md) |
| ADR-012 | IRT / adaptive-testing implementation | §27 | PENDING | To be resolved in Epic 5 |
| ADR-013 | Readiness-calibration methodology | §27, FR-020 | PENDING | To be resolved in Epic 8 |
| ADR-014 | Multimodal generation provider(s) | §27, FR-016 | PENDING | To be resolved in Epic 8 |

## Additional architecture decisions (implied by PRD but not explicitly named in §27)

| ID | Decision | PRD Reference | Status | Record File |
|---|---|---|---|---|
| ADR-015 | Repository/service boundary — modular monolith | §28 | PENDING | To be resolved in Epic 0.2 |
| **ADR-016** | Learning-state machine implementation | §13, FR-001 | **ACCEPTED** | [ADR-016-learning-state-machine.md](./ADR-016-learning-state-machine.md) |
| ADR-017 | Structured-output validation framework for LLM outputs | FR-010 | **ACCEPTED** | [ADR-006-llm-provider-abstraction.md](./ADR-006-llm-provider-abstraction.md) |
| ADR-018 | RAG chunking/embedding parameters | FR-005, FR-008 | PENDING | To be resolved in Epic 3 |
| ADR-019 | Frontend HTTP & Data Fetching Strategy (TanStack Query v5) | Frontend Track | **ACCEPTED** | [ADR-008-frontend-framework-and-ui-stack.md](./ADR-008-frontend-framework-and-ui-stack.md) |
| ADR-020 | Frontend State Management Strategy (Zustand) | Frontend Track | **ACCEPTED** | [ADR-008-frontend-framework-and-ui-stack.md](./ADR-008-frontend-framework-and-ui-stack.md) |
