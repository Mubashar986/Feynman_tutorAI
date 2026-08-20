# Backend Developer Track Guide
## AI Adaptive Exam Learning Platform

This guide outlines the responsibilities, tech stack, and protocols for the Backend Developer track.

### 1. Backend Stack Foundation
The backend track is built upon a modern Python ecosystem optimized for performance, type safety, and async operations.
- **Framework:** FastAPI (for high-performance asynchronous API endpoints)
- **Language:** Python 3.12+ (leveraging modern type hinting features)
- **ORM & Database:** SQLModel / SQLAlchemy 2.0 with PostgreSQL
- **Migrations:** Alembic
- **Validation:** Pydantic V2
- **Background Jobs:** Celery, RQ, or similar (pending ADR)
- **Caching:** Redis (pending ADR)

### 2. Backend Directory Structure
The backend codebase follows a domain-driven design architecture.

```text
backend/
├── app/
│   ├── api/            # API routing and endpoint definitions
│   ├── core/           # Configuration, security, and global settings
│   ├── db/             # Database session management and migrations
│   ├── domains/        # Domain logic (e.g., users, exams, learning_state)
│   │   ├── users/
│   │   ├── exams/
│   │   └── state/
│   ├── models/         # SQLModel database schemas
│   ├── schemas/        # Pydantic validation schemas (API contracts)
│   ├── services/       # Cross-domain business logic and third-party integrations (LLMs)
│   └── workers/        # Asynchronous background tasks
├── tests/              # Pytest suite
└── requirements.txt / pyproject.toml
```

### 3. Backend Stage Lifecycle Adaptations
When applying the project's stage-gated lifecycle to backend tasks:
- **Stage 1 (Conceptual):** Focus on data flow, state machine transitions, and database isolation strategies. Ensure no LLM output directly modifies canonical state without validation.
- **Stage 2 (Design):** Define precise Pydantic schemas. Generate the OpenAPI spec to fulfill the Contract-First protocol. Plan the database schema changes and draft the Alembic migration.
- **Stage 3 (Implementation):** Implement the domain logic, ensuring strict separation of concerns (routers vs. services vs. data access).
- **Stage 4 (Validation):** Write Pytest test cases covering success, failure, and edge cases. Ensure security constraints (RBAC) are verified.

### 4. Backend-Specific Rules & Constraints
- **Provider Abstraction:** Never embed specific LLM provider calls (e.g., `openai.ChatCompletion.create`) directly in domain logic. Always route through an abstraction layer.
- **Atomic State Transitions:** Updates to a student's learning state must be atomic and transacted to prevent inconsistent data.
- **Server-Side RBAC:** Never trust client-provided roles. Enforce all access controls securely on the server.
- **LLM as Component:** Treat LLMs as unreliable sub-components. Validate all structured outputs.

### 5. Responsibilities
- **API Design:** Designing RESTful endpoints and generating OpenAPI contracts for the frontend.
- **Domain Logic:** Implementing the complex educational and psychometric algorithms (IRT math).
- **Database Schema:** Designing efficient, scalable, and isolated relational models.
- **Worker Jobs:** Orchestrating async tasks like PDF parsing, batch grading, or report generation.

### 6. Contract Production
To produce API contracts:
1. Define Pydantic models for Requests and Responses in `app/schemas/`.
2. Use FastAPI's routing to bind these models to endpoints.
3. FastAPI automatically generates `/openapi.json`.
4. Export this schema and copy it to `docs/contracts/schemas/` for the frontend team.

### 7. Testing Strategy
- Use `pytest` for all unit and integration testing.
- Use `httpx.AsyncClient` for testing API endpoints.
- Mock external services (database, LLM providers) during unit tests.

### 8. Relevant Decision Registries
As a backend developer, you must actively manage and consult:
- **ADR-INDEX.md:** For foundational architecture decisions.
- **DDR-INDEX.md:** For data schemas, migrations, and isolation strategies.
- **SDR-INDEX.md:** For core algorithmic and system design decisions.
- **AIDR-INDEX.md:** For LLM integration and prompt engineering strategies.
