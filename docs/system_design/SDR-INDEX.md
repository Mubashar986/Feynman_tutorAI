# System Design Records (SDR) Index

Status legend: `PENDING` (not started) · `IN_PROGRESS` · `PROPOSED` (generated, awaiting user acceptance) · `ACCEPTED` · `SUPERSEDED`

## What are SDRs?
System Design Records (SDRs) govern the design and architecture of domain logic, state machines, algorithms, mathematical models, and pipelines. They are not overarching foundational decisions (like an ADR) but rather deep dives into specific complex system components required to fulfill product requirements.

SDRs are created **just-in-time** when a Work Breakdown Structure (WBS) task requires them. They evolve during development and are not pre-decided. New rows are added as new system designs surface.

## Existing SDRs

| ID | System Design Record Title | Domain/Component | PRD Reference | Status |
|---|---|---|---|---|
| SDR-001 | Learning-State Machine Engine | Core Learning | PRD §13, FR-001 | PENDING |
| SDR-002 | Student Mastery & Adaptive IRT Math | IRT Engine | PRD §8, FR-003 | PENDING |
| SDR-003 | Exam Template & Curriculum Hierarchy | Curriculum | PRD §5, FR-002 | PENDING |
| SDR-004 | Question Laboratory & Quality Pipeline | Content Gen | PRD §12, FR-004/FR-015 | PENDING |
| SDR-005 | AI Quality-Control & Guardrail Engine | AI Safety | PRD §14, FR-010 | PENDING |
| SDR-006 | Resource Ingestion & PDF/OCR Pipeline | Ingestion | PRD §11, FR-005 | PENDING |
| SDR-007 | Grounded Tutor & Hybrid RAG Retrieval | Retrieval | PRD §14.3, FR-008 | PENDING |
| SDR-008 | Past-Paper & Blueprint Intelligence | Analysis | PRD §14.2, FR-014 | PENDING |
| SDR-009 | Error Bank & Misconception Graph | Diagnosis | PRD §10, FR-006/FR-012 | PENDING |
| SDR-010 | Spaced Repetition & Revision Engine | Memory | FR-007 | PENDING |
| SDR-011 | Specialized Pedagogical Modes (Teach-Back, Adversarial, Why-Wrong) | Modes | FR-017/018/019 | PENDING |
| SDR-012 | Personal Learning Twin Profile | Profiles | FR-011 | PENDING |
| SDR-013 | Dynamic Knowledge Map Graph | Knowledge Graph | FR-013 | PENDING |
| SDR-014 | Multimodal Content Pipeline | Content Gen | FR-016 | PENDING |
| SDR-015 | Exam Readiness Simulator Engine | Readiness | FR-020 | PENDING |
| SDR-016 | Relational Data Model & Audit Schema | Data Model | PRD §9, NFR-006 | PENDING |
| SDR-017 | API Architecture & Server-Side RBAC | Security / API | PRD §18, FR-021 | PENDING |
| SDR-018 | Async Worker Pipelines & DLQ Policies | Background Jobs | PRD §19 | PENDING |
| SDR-019 | Observability, Tracing & Cost Telemetry | Operations | PRD §23, FR-024/025 | PENDING |
| SDR-020 | Multi-Tenant Isolation & Version Immutability | Tenancy | FR-022, NFR-006 | PENDING |
