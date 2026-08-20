# ADR-004: Background Task Framework & Message Broker — ARQ / Taskiq with Redis

## 1. Context & Problem Statement
The platform has several heavy, asynchronous background workloads (PRD §19, §27):
* Document text extraction, chunking, and vector embedding generation (PDF ingestion).
* Batch assessment item generation and quality validation passes.
* Spaced repetition decay and daily revision queue recalculations.
* Analytical aggregation and readiness score calculations.

Interactive FastAPI requests must not block on these operations (PRD NFR-001, NFR-003). We need a lightweight, robust, async-native background worker and message broker that runs seamlessly on Windows without process fork failures and integrates directly with Python `asyncio`.

## 2. Decision
Adopt **ARQ (Async Redis Queue)** / **Taskiq** with **Redis** as the message broker and task state store. For lightweight fire-and-forget operations (e.g. audit log flushes, non-blocking telemetry), use FastAPI's built-in `BackgroundTasks`.

## 3. Evaluated Alternatives

### Option A: ARQ / Taskiq on Redis (Recommended)
* **Description:** Pure `asyncio` distributed task queue designed natively for modern Python async frameworks.
* **Pros:** 100% async-native, runs flawlessly on Windows without multiprocessing/billiard hacks, lightweight, zero Celery bloat, high throughput, trivial job serialization via MessagePack/JSON.
* **Cons:** Requires Redis broker in production.
* **Mandatory Gates:** Passes all 10 gates.
* **Score:** 84/85.

### Option B: Celery + RabbitMQ / Redis
* **Description:** Traditional Python distributed task queue.
* **Pros:** Established enterprise ecosystem.
* **Cons:** `billiard` multiprocessing process-fork issues on Windows (requires awkward `solo` / `threads` workarounds), synchronous worker model clashes with FastAPI async database sessions, heavy operational overhead.
* **Mandatory Gates:** Passes gates, but creates high Windows developer friction.
* **Score:** 52/85.

### Option C: In-Process FastAPI BackgroundTasks Only
* **Description:** Run all tasks inside the FastAPI web server process.
* **Pros:** Zero external dependencies.
* **Cons:** Heavy PDF parsing or bulk LLM generation can block the web server event loop or consume all container memory, tasks are lost if the server process restarts.
* **Mandatory Gates:** Fails reliability for heavy batch jobs.
* **Score:** 55/85.

## 4. Quality Control Matrix & Gate Evaluation

| Control | Option A (ARQ on Redis) | Option B (Celery) | Option C (FastAPI In-Process Only) |
| :--- | :--- | :--- | :--- |
| **PRD Alignment** | 5 (Matches §19, §27) | 4 (Meets requirements) | 2 (Cannot handle heavy jobs) |
| **Async Native (FastAPI)**| 5 (Pure asyncio) | 2 (Sync thread pools) | 5 (Native asyncio) |
| **Windows Ergonomics** | 5 (Clean execution) | 1 (Multiprocessing fork crashes) | 5 (No setup) |
| **Reliability** | 5 (Redis persisted queue)| 5 (Mature queue) | 2 (Tasks lost on restart) |
| **Gate 1–10 Status** | **PASS (All 10)** | PASS | PASS |

## 5. Consequences & Implementation Blueprint
* Worker defined under `backend/app/workers/task_worker.py`.
* Async job enqueue helpers injected via FastAPI dependency.
* In local dev without Redis, tasks can be executed synchronously or via `BackgroundTasks` fallback.

```yaml
adr_id: ADR-004
title: "Background Task Framework & Message Broker — ARQ with Redis"
decision_level: "Infrastructure / Async Processing"
status: accepted
date: "2026-08-20"
depends_on: [ADR-002]
supersedes: []
gates:
  - id: 7
    result: pass
    evidence: "Isolates untrusted PDF parsing and OCR jobs into background worker processes"
recommended_option: "Option A: ARQ / Taskiq on Redis"
priority_tier_used_for_tiebreak: "Tier 5 (Maintainability & Windows Ergonomics)"
open_assumptions: []
```
