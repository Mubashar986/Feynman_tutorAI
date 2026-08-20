---
description: Run the full WBS-first, stage-gated, decision-gated, error-locked development lifecycle for a task on the AI Adaptive Exam Learning Platform.
---

# DevCycle Workflow

This is an ENHANCED version of the development lifecycle. When the user types `/devcycle <task or idea>`, orchestrate strictly using `AGENTS.md` and the skills under `.agents/skills/`.

## Core Execution Sequence

1. **Load Constraints:** Load `AGENTS.md` in full. Restate the active constraints from §1.2 (decision-first execution) and §1.3 (non-negotiable product constraints) before doing anything else.

2. **WBS Check:** Check `.agents/state/current_task.md`. If no active WBS leaf task matches the `<task or idea>`, execute the `roadmap-wbs-planner` skill (Stage 0). **STOP** and wait for explicit user approval of the WBS before continuing.

3. **Conceptual Understanding:** Execute the `conceptual-understanding` skill (Stage 1) for the approved leaf task.

4. **Living Decision Registry Checks:** Check `docs/adr/ADR-INDEX.md` and related indexes (DDR, AIDR, FDR).
   - If this task depends on any decision marked `PENDING`, involves choosing between competing patterns, or requires a difficult defect fix — execute `adr-generator` or `narrsistic-pluto`.
   - **STOP** for user acceptance. Update indices and `.agents/state/decisions.md` only after acceptance.

5. **Codebase Design (Stage 2):** Execute the `codebase-design` skill. No code changes yet.
   - **Two-Developer Track Awareness:** If the task spans multiple tracks, tag the design with `[BACKEND]` or `[FRONTEND]`.
   - **Contract-First Protocol:** Ensure cross-track dependencies define their API contracts before any track implements logic.
   - **STOP** and wait for explicit user approval.

6. **CS Domain Learning (Stage 3):** If the task touches adaptive-learning algorithms, IRT, RAG, misconception reasoning, embeddings, or unfamiliar behavior — execute `cs-domain-learning`.
   - **STOP** and present Stage 1–3 artifacts together.

7. **Implementation (Stage 4 - Coding):** Implement strictly according to the approved Stage 2 design.
   - **Terminal Command Error Lock:** Enforced at every stage. If ANY terminal command fails, halt the devcycle and immediately trigger `/incident-rca`. No proceeding past errors.
   - **Zero Silent Library Ingestion:** Do not introduce ANY dependency or architectural pattern not covered by an accepted ADR. Stop and flag it instead.
   - **Full-File Inspection:** Inspect all modified files fully before finishing implementation to ensure zero drift.

8. **QA & Verification (Stage 5):** Execute the `testing-verification` and `qa-audit` workflows.

9. **Completion:** Update `.agents/state/current_task.md`, `current_stage.md`, `decisions.md`, and `docs/adr/ADR-INDEX.md`. Report completion using the Agent Response Contract format.
