# ADR-002: Redis Usage & Caching Strategy

## 1. Context & Problem Statement
The platform requires caching for frequently accessed, read-heavy resources (such as active Exam Templates, syllabus topic trees, and user session validation) as well as distributed rate-limiting for LLM endpoints (PRD §27, NFR-001, NFR-003). The caching layer must not store canonical student learning state (which must live in the ACID primary database per PRD Constraint #1 & #3) and must degrade gracefully if the cache is temporarily unavailable.

## 2. Decision
Adopt **Redis** as a secondary cache, distributed rate-limiter, and async queue backend, operated via `redis.asyncio`. Provide an automatic **in-memory Cache fallback** for offline unit testing and single-process local development.

## 3. Evaluated Alternatives

### Option A: Redis via `redis.asyncio` with In-Memory Dev Fallback (Recommended)
* **Description:** Redis server in production with an abstracted `CacheService` interface that falls back to in-memory TTL caching when Redis is disabled in local settings.
* **Pros:** Blazing fast sub-millisecond lookups, distributed token-bucket rate limiting across API replicas, shared backend for async task queuing (ARQ).
* **Cons:** Additional operational component in production.
* **Mandatory Gates:** Passes all 10 gates.
* **Score:** 84/85.

### Option B: Canonical State in Redis
* **Description:** Store student active exam sessions and mastery state directly in Redis keys.
* **Pros:** Fast writes.
* **Cons:** Violates PRD Constraint #3 (state transitions must be auditable and relationally consistent). Risk of data loss on Redis eviction or restart.
* **Mandatory Gates:** Fails Gate 2 & 3.
* **Score:** 30/85 (Forbidden anti-pattern).

### Option C: In-Memory Application Caching Only (No Redis)
* **Description:** Use Python `lru_cache` / `cachetools` inside FastAPI memory.
* **Pros:** Zero setup.
* **Cons:** Cannot coordinate rate limits or shared caches across multiple FastAPI worker processes or replicas.
* **Mandatory Gates:** Passes gates, but fails multi-worker scalability (PRD NFR-001).
* **Score:** 60/85.

## 4. Quality Control Matrix & Gate Evaluation

| Control | Option A (Redis + Fallback) | Option B (Canonical Redis) | Option C (In-Memory Only) |
| :--- | :--- | :--- | :--- |
| **PRD Alignment** | 5 (Matches §27, NFR-001) | 1 (Violates §13 state rule) | 3 (Limited to 1 worker) |
| **Data Integrity** | 5 (Cache-aside pattern) | 1 (Eviction data loss) | 4 (Safe read-only) |
| **Scalability** | 5 (Multi-replica support) | 4 (Fast) | 2 (Per-process isolation) |
| **Gate 1–10 Status** | **PASS (All 10)** | FAIL | PASS |

## 5. Consequences & Implementation Blueprint
* `CacheService` created under `backend/app/core/cache.py`.
* Used strictly as a read-through / cache-aside store for static templates and rate limiting.
* Canonical learning states are never written solely to cache.

```yaml
adr_id: ADR-002
title: "Redis Usage & Caching Strategy"
decision_level: "Infrastructure / Performance"
status: accepted
date: "2026-08-20"
depends_on: [ADR-001]
supersedes: []
gates:
  - id: 3
    result: pass
    evidence: "Cache-aside design ensures learning state remains in primary ACID database"
recommended_option: "Option A: Redis via redis.asyncio with In-Memory Dev Fallback"
priority_tier_used_for_tiebreak: "Tier 2 (Correctness / Data Integrity)"
open_assumptions: []
```
