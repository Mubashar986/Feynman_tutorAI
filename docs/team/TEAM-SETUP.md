# AI Adaptive Exam Learning Platform
## Team Setup and Getting Started Guide

Welcome to the AI Adaptive Exam Learning Platform project. This document serves as the comprehensive guide for onboarding and understanding how the team operates, communicates, and builds the system.

### 1. Project Overview
The AI Adaptive Exam Learning Platform is an intelligent educational system designed to transform exam preparation from a passive chatbot experience into a structured, measurable, personalized learning journey. The platform uses AI for tutoring, grading, and content generation, all orchestrated by rigorous state machines, knowledge graphs, and Item Response Theory (IRT) mathematical models.

### 2. Team Structure
This project is executed by a two-person development team working in parallel tracks:

#### Developer 1 (Backend Track)
- **Role:** Backend Architect and Data Engineer
- **Core Stack:** FastAPI, Python 3.12+, SQLModel/SQLAlchemy, Alembic, Pydantic V2
- **Responsibilities:**
  - Designing the API architecture and contracts.
  - Implementing the core learning state machines and domain logic.
  - Managing database schemas and migrations.
  - Building asynchronous worker pipelines (e.g., Celery or RQ).
  - Integrating multi-vendor LLM capabilities via abstraction layers.
  - Implementing psychometric models and IRT math engines.

#### Developer 2 (Frontend Track)
- **Role:** Frontend Architect and UX Engineer
- **Core Stack:** React, TypeScript, Vite (or Next.js depending on FDR-001), Tailwind CSS
- **Responsibilities:**
  - Building accessible, responsive, and performant user interfaces.
  - Managing client-side state and caching.
  - Handling real-time data streaming (e.g., SSE for LLM responses).
  - Implementing component architectures based on design systems.
  - Ensuring strict type safety by consuming generated API contracts.
  - Creating visual data representations and mathematical rendering (LaTeX/Mermaid).

### 3. Shared Resources
To maintain alignment, the following directories and files are shared and govern both tracks:

- `.agents/`: Contains state files, decision logs, and agent prompts.
- `docs/`: The central repository for all architecture and design documentation.
- `AGENTS.md`: The manifesto detailing agentic workflows and AI-assisted development protocols.
- `GEMINI.md`: Guidelines and prompts specific to Gemini LLM usage.

### 4. Agentic Workflow and Lifecycle
Both developers utilize an AI-assisted agentic workflow following a strict stage-gated lifecycle:

- **Stage 0 (WBS):** Break down features into granular, atomic tasks. Establish the roadmap.
- **Stage 1 (Conceptual):** Map out state transitions, data flows, and physical analogies before writing code.
- **Pluto (RCA):** The mandatory Root Cause Analysis phase triggered on any build failure or architectural inconsistency.
- **Stage 2 (Design):** Define contracts, schemas, interfaces, and component hierarchies.
- **Stage 3 (Implementation):** Write the code, strictly adhering to Stage 2 contracts.
- **Stage 4 (Validation):** Automated and manual testing to confirm requirements are met.

### 5. Protective Mechanisms
Both developers operate under strict protective rules to ensure code quality:

- **Terminal Error Lock:** Any terminal error (build failure, type error, test failure) immediately halts progression to the next stage until a Root Cause Analysis (Pluto) is completed.
- **Zero-Silent-Deps:** No new third-party dependency can be added without explicitly evaluating alternatives and recording the decision. Defaulting to familiar tools (like Axios or Redux) without consideration is prohibited.
- **Full-File Inspection:** Agents and developers must inspect entire files before modifying them to prevent unintended side effects or loss of context.

### 6. Work Breakdown Structure (WBS) Tagging
Tasks in the project management system (or `roadmap.md`) are explicitly tagged to indicate responsibility:
- `[BACKEND]`: Tasks solely for Developer 1.
- `[FRONTEND]`: Tasks solely for Developer 2.
- `[SHARED]`: Tasks requiring coordinated effort, contract negotiation, or mutual awareness (e.g., defining a new cross-cutting feature like authentication).

### 7. Communication Protocol
Effective communication is critical for parallel tracks:

- **API Contracts:** The sole source of truth for API communication is `docs/contracts/` where OpenAPI schemas reside.
- **Decisions:** Accepted architectural decisions are logged in `.agents/state/decisions.md` and detailed in the respective `docs/*_design/` directories.
- **Issues:** Cross-track bugs or integration problems are tracked in `.agents/state/issues.md`.
- **Syncs:** Major changes to shared models, state machines, or contracts require explicit notification to the other developer.

### 8. Directory Structure
Understanding the workspace layout is essential:

```text
c:/Users/Mubashar/Desktop/Curious_Feynman/
├── backend/               # Backend Python/FastAPI codebase
├── frontend/              # Frontend React/TypeScript codebase
├── docs/                  # Project documentation and decision registries
│   ├── adr/               # Architecture Decision Records
│   ├── ai_design/         # AI Decision Records (AIDR)
│   ├── contracts/         # Shared API schemas and protocols
│   ├── data_design/       # Data Decision Records (DDR)
│   ├── frontend_design/   # Frontend Decision Records (FDR)
│   ├── system_design/     # System Design Records (SDR)
│   └── team/              # Team setup and track guidelines (this directory)
├── .agents/               # Agent state and workflow configuration
├── AI_Adaptive_Exam_Learning_Platform_PRD_SRS.md  # Core Requirements
└── ...
```

### 9. Getting Started Steps

1. **Read Core Documents:** Carefully review `AGENTS.md` and `GEMINI.md` to internalize the AI-assisted development philosophy.
2. **Review Open Decisions:** Read `docs/adr/ADR-INDEX.md` and other relevant index files to understand the current architectural landscape and pending decisions.
3. **Generate Roadmap:** Run the Stage 0 (WBS) process to generate the initial project roadmap if it doesn't exist.
4. **Select Task:** Begin with the recommended first task assigned to your track (`[BACKEND]` or `[FRONTEND]`).
5. **Follow Lifecycle:** Adhere strictly to the Stage 1 -> Stage 4 lifecycle for your chosen task.

### 10. Conclusion
By adhering to these structures, protocols, and workflows, the team can move rapidly and independently while ensuring a cohesive, robust, and high-quality final product. Quality is not an afterthought; it is built into the process.
