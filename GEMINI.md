# Global Rules — AI Adaptive Exam Learning Platform

This file is loaded for every conversation in this workspace. Its purpose is to guarantee the hardest constraints hold even if a skill isn't triggered or `AGENTS.md` isn't picked up for some reason — treat it as a backstop, not a replacement for `AGENTS.md`.

**Always check for `AGENTS.md` in the project workspace root first and load it in full before any planning or implementation.** It is the operating contract for this project. If nested `AGENTS.md` files exist in subfolders, load those too for work inside that folder.

## 1. Non-Negotiable Product Constraints

These are permanent, drawn directly from the PRD, and apply regardless of which WBS task is active. No design or task may propose violating one:

1. LLM output must not directly become official learning state (PRD §14.4, FR-001, FR-010).
2. Student state must be isolated per student and exam (PRD §5.2, FR-022, NFR-002).
3. Learning-state transitions must be valid, application-enforced, and auditable (PRD FR-001, §13, FR-025).
4. Generated questions must be validated before student use (PRD FR-004, FR-015).
5. Source-grounded answers must use retrieval before generation (PRD §14.3, FR-008).
6. Role-based access must be enforced server-side (PRD FR-021, NFR-005).
7. Uploaded files must be treated as untrusted input (PRD NFR-005, FR-005).
8. The system must not silently advance a student after a critical failure (PRD NFR-004).
9. Important learning decisions must be explainable (PRD NFR-008, FR-025).
10. Provider-specific logic must not be embedded in core learning logic (PRD FR-023, NFR-007).

## 2. Terminal Command Error Lock
- ANY error in terminal execution (build, test, lint, script, runtime) means the agent **IMMEDIATELY HALTS** all other work. 
- It must invoke the `narrsistic-pluto` skill for full 5-Whys/Fishbone Root Cause Analysis before resuming. 
- The error must be logged in `.agents/state/issues.md`.
- A disappearing error is NOT automatically resolved.

## 3. Zero Silent Library/Dependency Ingestion
- The agent is STRICTLY FORBIDDEN from introducing ANY library, SDK, package, or dependency by habit or assumption.
- Must evaluate platform primitives first, then compare 3-5 alternatives (bundle size, CVE history, type safety, maintenance).
- Must get explicit user approval in Stage 2 Design before any `npm install` or `pip install`.

## 4. Full-File Inspection Mandate
- Before modifying ANY file, the agent MUST read the ENTIRE file (all imports, class definitions, functions, exports). 
- Before changing any function signature or return type, the agent MUST search for and inspect ALL callers and consumers across the repository. 
- No grep-snippet-based edits. No hallucinated file contents. 
- Every claim about code must be tagged VERIFIED (read from disk this turn), INFERRED (requires confirmation), or UNVERIFIED (prohibited as basis for edits).

## 5. Two-Developer Team Awareness
- This is a 2-person team (Backend: FastAPI/Python, Frontend: React/TypeScript). 
- Both tracks share `.agents/state/`, `docs/`, and `.agents/rules/`. 
- Contract-first development: Backend produces OpenAPI schemas first, Frontend generates TypeScript types from them.

## 6. Living Decision Registry Protocol
- Decisions evolve during development. 
- When any task surfaces a new decision point (tech, data, AI, or frontend), the agent HALTS, evaluates via Narrsistic Pluto, generates a formal decision record (ADR/DDR/AIDR/FDR), and waits for user acceptance before proceeding.

## 7. Operating Contract
- Reference `AGENTS.md` for complete operating contract details.
