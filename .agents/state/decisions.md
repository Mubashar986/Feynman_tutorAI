# Durable Architectural & Engineering Decisions — AI Adaptive Exam Learning Platform

This file records all formally accepted architectural and technical decisions governing the platform.

---

## DECISION-000: MVP Capability Slice (3-Phase Milestone Structure)
* **Status:** ACCEPTED (2026-08-20)
* **Record:** [docs/adr/ADR-000-mvp-capability-slice.md](file:///c:/Users/Mubashar/Desktop/Curious_Feynman/docs/adr/ADR-000-mvp-capability-slice.md)
* **Summary:** The product roadmap is strictly divided into 3 phases. Phase 1 delivers the closed learning loop: Exam Template Engine (Cap 2), Student Learning State Machine (Cap 3, §13), Question Lab & Assessment Engine (Cap 4, 15), Resource Ingestion & Vector RAG (Cap 5, 8), Grounded Socratic AI Tutor with SSE streaming (Cap 8, 10), Error Bank (Cap 6), and Distraction-Free Exam Player with KaTeX math rendering (§17). Advanced modes (Teach-Back, Adversarial, Misconception DAG) and Readiness Simulation follow in Phases 2 and 3.

---

## DECISION-001: Primary Database Technology (PostgreSQL + SQLModel / SQLite Dev)
* **Status:** ACCEPTED (2026-08-20)
* **Record:** [docs/adr/ADR-001-primary-database.md](file:///c:/Users/Mubashar/Desktop/Curious_Feynman/docs/adr/ADR-001-primary-database.md)
* **Summary:** PostgreSQL is the primary transactional ACID system of record, managed via SQLModel (SQLAlchemy 2.0 async + Pydantic V2) and Alembic migrations. SQLite async (`aiosqlite`) is supported in dual-mode for zero-setup local dev and in-memory test fixtures.

---

## DECISION-002: Redis Usage & Caching Strategy
* **Status:** ACCEPTED (2026-08-20)
* **Record:** [docs/adr/ADR-002-caching-strategy.md](file:///c:/Users/Mubashar/Desktop/Curious_Feynman/docs/adr/ADR-002-caching-strategy.md)
* **Summary:** Redis is used for cache-aside static template caching, distributed rate-limiting, and async queue persistence via `redis.asyncio`. In-memory TTL cache fallback is provided for offline testing. Canonical student learning state is never written solely to cache.

---

## DECISION-003: Vector Database Technology (Qdrant Local Disk & Remote Adapter)
* **Status:** ACCEPTED (2026-08-20)
* **Record:** [docs/adr/ADR-003-vector-database.md](file:///c:/Users/Mubashar/Desktop/Curious_Feynman/docs/adr/ADR-003-vector-database.md)
* **Summary:** Qdrant is adopted behind an abstracted `VectorStoreBase` protocol. Local disk persistence (`path="./data/vector_db"`) or in-memory mode (`":memory:"`) is used for Windows development and automated testing without Docker/C++ compiler dependencies. Remote Qdrant server is used for production.

---

## DECISION-004: Background Task Framework & Message Broker (ARQ on Redis)
* **Status:** ACCEPTED (2026-08-20)
* **Record:** [docs/adr/ADR-004-background-tasks-and-broker.md](file:///c:/Users/Mubashar/Desktop/Curious_Feynman/docs/adr/ADR-004-background-tasks-and-broker.md)
* **Summary:** ARQ (Async Redis Queue) / Taskiq with Redis broker is chosen over Celery to provide pure async-native job processing without Windows multiprocessing fork failures. FastAPI `BackgroundTasks` handles lightweight non-blocking telemetry and audit flushes.

---

## DECISION-006: Multi-Provider LLM Gateway & Pydantic Validation Engine
* **Status:** ACCEPTED (2026-08-20)
* **Record:** [docs/adr/ADR-006-llm-provider-abstraction.md](file:///c:/Users/Mubashar/Desktop/Curious_Feynman/docs/adr/ADR-006-llm-provider-abstraction.md)
* **Summary:** An async Multi-Provider LLM Gateway (`LLMProviderBase`) abstracts Google Gemini, OpenAI, Anthropic, and local Ollama with dynamic fallback on rate limits. All structured outputs pass through strict Pydantic V2 schema validation before touching canonical domain models (enforcing PRD Constraint #1 & #10).

---

## DECISION-008: Frontend Framework & UI Library Ecosystem
* **Status:** ACCEPTED (2026-08-20)
* **Record:** [docs/adr/ADR-008-frontend-framework-and-ui-stack.md](file:///c:/Users/Mubashar/Desktop/Curious_Feynman/docs/adr/ADR-008-frontend-framework-and-ui-stack.md)
* **Summary:** Frontend is built with React 18+, Vite, TypeScript (Strict Mode), Tailwind CSS, and Shadcn UI (Radix primitives). Specialized packages include `react-katex` for LaTeX mathematical formulas, `@xyflow/react` (React Flow) for knowledge maps, `TanStack Query v5` for API caching, and `Zustand` for client UI state. Design specifications codified in `docs/frontend_design/DESIGN_SYSTEM_TYPOGRAPHY.md`.
