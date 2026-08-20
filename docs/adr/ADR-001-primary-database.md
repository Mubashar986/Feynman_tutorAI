# ADR-001: Primary Database Technology — PostgreSQL with SQLModel / Async SQLAlchemy (Dual-Mode SQLite Support)

## 1. Context & Problem Statement
The platform requires a primary transactional system of record to store users, roles, exam templates, curricula, questions, attempts, student mastery states, error logs, and audit trails (PRD §9, §20, §27). The database must enforce strict ACID guarantees, foreign key integrity, and support asynchronous I/O with FastAPI (`asyncio`). It must also offer seamless local development on Windows without requiring heavy infrastructure for basic unit tests.

## 2. Decision
Adopt **PostgreSQL** as the primary production database, managed via **SQLModel** (which combines Pydantic V2 and SQLAlchemy 2.0 async) and **Alembic** migrations. Support **SQLite (`aiosqlite`)** in dual-mode configuration for zero-setup local developer onboarding and blazing-fast in-memory test fixtures.

## 3. Evaluated Alternatives

### Option A: PostgreSQL via SQLModel / Async SQLAlchemy (Recommended)
* **Description:** Standard relational ACID database with async Python ORM.
* **Pros:** Strict relational integrity, foreign keys, cascading constraints, schema migrations with Alembic, native async I/O via `asyncpg`, seamless in-memory SQLite fallback for tests.
* **Cons:** Requires running PostgreSQL server in production/staging.
* **Mandatory Gates:** Passes all 10 gates.
* **Score:** 83/85.

### Option B: MongoDB / Document Store
* **Description:** NoSQL document database storing student state and exam templates as JSON documents.
* **Pros:** Schema flexibility for question payloads.
* **Cons:** Lacks strict cross-collection relational constraints, risk of data inconsistency during complex mastery state updates (PRD §13), weak auditability for multi-entity transactions.
* **Mandatory Gates:** Fails Gate 2 & 3 under high concurrency without distributed transactions.
* **Score:** 48/85.

### Option C: Pure SQLite File Only
* **Description:** Use SQLite file exclusively for all environments.
* **Pros:** Zero configuration, works natively everywhere.
* **Cons:** Database-level write lock limits concurrency for multi-student production scale (PRD NFR-001).
* **Mandatory Gates:** Passes gates, but fails long-term scalability.
* **Score:** 58/85.

## 4. Quality Control Matrix & Gate Evaluation

| Control | Option A (PostgreSQL + SQLModel) | Option B (MongoDB) | Option C (Pure SQLite) |
| :--- | :--- | :--- | :--- |
| **PRD Alignment** | 5 (Matches §9, §20, §27) | 3 (Loose relational model) | 3 (Concurrency limits) |
| **Data Integrity** | 5 (ACID + Foreign Keys) | 2 (Eventual consistency) | 4 (ACID but single writer) |
| **Auditability** | 5 (Immutable event logs) | 3 (Document history) | 4 (Standard tables) |
| **Performance** | 5 (Async connection pool) | 4 (Fast reads) | 2 (Write bottlenecks) |
| **Gate 1–10 Status** | **PASS (All 10)** | FAIL | PASS |

## 5. Consequences & Implementation Blueprint
* Models defined in `backend/app/models/` using `SQLModel`.
* Migrations managed with `alembic`.
* Database engine instantiated dynamically based on `settings.DATABASE_URL` (PostgreSQL `postgresql+asyncpg://` or SQLite `sqlite+aiosqlite://`).

```yaml
adr_id: ADR-001
title: "Primary Database Technology — PostgreSQL with SQLModel / Async SQLAlchemy"
decision_level: "Infrastructure / System of Record"
status: accepted
date: "2026-08-20"
depends_on: [ADR-000]
supersedes: []
gates:
  - id: 2
    result: pass
    evidence: "Enforces strict student_id and exam_template_id foreign key relational isolation"
  - id: 3
    result: pass
    evidence: "Atomic transactions guarantee state transitions and audit logs commit together"
  - id: 6
    result: pass
    evidence: "User and role tables support server-side RBAC enforcement"
recommended_option: "Option A: PostgreSQL via SQLModel / Async SQLAlchemy (Dual-Mode SQLite)"
priority_tier_used_for_tiebreak: "Tier 2 (Correctness / Data Integrity / Reliability)"
open_assumptions: []
```
