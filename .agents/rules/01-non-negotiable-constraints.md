---
name: non-negotiable-constraints
description: Enforces the 10 non-negotiable product constraints from the PRD that apply regardless of task or stage.
---

# Rule 01: Non-Negotiable Product Constraints

This rule enforces the 10 core product constraints defined in the PRD and `AGENTS.md` §1.3. These constraints apply permanently across all WBS tasks, epic definitions, and implementation stages. 

**No WBS task, codebase design, or architectural decision may propose violating any of these constraints. If a task or user request appears to require it, STOP and escalate immediately.**

---

## Constraint 1: LLM output must not directly become official learning state
- **WHAT it means:** The unverified output of an LLM generation call (e.g., scoring an answer or determining a concept is known) cannot directly update the database state of the user's mastery.
- **WHY it exists:** (PRD §14.4, FR-001, FR-010) LLMs are non-deterministic and hallucinate. Using their direct output for mission-critical learning states corrupts the learning engine's integrity.
- **WHAT the agent must do:** Ensure LLM output is wrapped in a structured-output validation framework. Pass the validated output into a separate application-layer function that executes state transition logic.
- **WHAT happens if violated:** STOP the current task and flag a `CRITICAL` risk issue. Wait for architectural review.
- **EXAMPLE Violation:** Directly saving a JSON payload returned from OpenAI directly into the PostgreSQL `StudentMastery` table without Pydantic validation and mastery-engine boundary checks.

## Constraint 2: Student state isolated per student and exam
- **WHAT it means:** A student's interactions, mastery metrics, and session states are strictly sandboxed. 
- **WHY it exists:** (PRD §5.2, FR-022, NFR-002) One student's actions must not pollute the learning engine of another student taking the same exam.
- **WHAT the agent must do:** Design database schemas with compound keys (Student ID + Exam ID) and ensure API endpoints strictly enforce these bounds on all queries.
- **WHAT happens if violated:** HALT implementation. Re-design the domain boundary and update the issue register with a data-leakage risk.
- **EXAMPLE Violation:** Updating a shared global exam "average score" immediately upon a single student's test submission without isolating the student's individual state context first.

## Constraint 3: Learning-state transitions must be valid, application-enforced, auditable
- **WHAT it means:** Progressions (e.g., moving from "Beginner" to "Intermediate" in a topic) must run through strict finite-state machine (FSM) rules coded in the application.
- **WHY it exists:** (PRD FR-001, §13, FR-025) To prevent illegal transitions and maintain auditability for educational efficacy.
- **WHAT the agent must do:** Use enums, strict state machines, and audit-logging middleware for all learning-state modifications.
- **WHAT happens if violated:** Re-enter Stage 2 (Design) to introduce strict validation and state machines.
- **EXAMPLE Violation:** An API endpoint that allows the client to explicitly set `mastery_level = 100` via a POST request without going through the testing/assessment engine.

## Constraint 4: Generated questions validated before student use
- **WHAT it means:** Any AI-generated exam question must pass through a strict quality-control pipeline before the student ever sees it.
- **WHY it exists:** (PRD FR-004, FR-015) Presenting factually incorrect or poorly formatted questions actively harms learning and damages trust.
- **WHAT the agent must do:** Implement asynchronous generation flows. Questions must be generated, validated by a secondary process/LLM, and marked as `READY` in the database.
- **WHAT happens if violated:** Treat as an incident. Invoke Narrsistic Pluto for Root Cause Analysis on why the validation pipeline was skipped.
- **EXAMPLE Violation:** Streaming an AI-generated question directly to the frontend chat UI before storing and validating the syllabus alignment.

## Constraint 5: Source-grounded answers must use retrieval before generation
- **WHAT it means:** The LLM cannot simply "answer" from its weights. It must retrieve context from the specific Exam's authoritative resources (RAG).
- **WHY it exists:** (PRD §14.3, FR-008) Hallucinated answers in test prep cause failure. Grounds must be cited.
- **WHAT the agent must do:** Implement RAG pipelines. Ensure context strings are explicitly passed into the generation prompt.
- **WHAT happens if violated:** STOP and re-architect the service layer. Ensure vector retrieval is a mandatory prerequisite for the generation step.
- **EXAMPLE Violation:** Passing a student's question directly to the `/chat/completions` API without performing a similarity search on the knowledge base first.

## Constraint 6: Role-based access enforced server-side
- **WHAT it means:** Students, Administrators, and System Admins must have strict RBAC enforced at the API route layer, not just the frontend UI.
- **WHY it exists:** (PRD FR-021, NFR-005) Security and data protection.
- **WHAT the agent must do:** Use FastAPI dependency injection to check JWT scopes and roles before executing any business logic.
- **WHAT happens if violated:** Log a `CRITICAL` vulnerability issue and halt all non-security WBS tasks.
- **EXAMPLE Violation:** A `GET /api/v1/exams/{id}/content` route that relies on the frontend client to hide the "Edit Exam" button instead of checking permissions server-side.

## Constraint 7: Uploaded files treated as untrusted input
- **WHAT it means:** PDFs, images, or text uploaded for resources/past papers must be sanitized and verified.
- **WHY it exists:** (PRD NFR-005, FR-005) To prevent arbitrary code execution, prompt injection, or malicious data ingestion.
- **WHAT the agent must do:** Implement file-type validation, size limits, and sanitization before processing with extraction tools or embeddings.
- **WHAT happens if violated:** Escalate to QA and re-enter Stage 2 to build security middleware.
- **EXAMPLE Violation:** Blindly executing an OCR script or passing raw document bytes directly into a database without MIME-type validation.

## Constraint 8: System must not silently advance student after critical failure
- **WHAT it means:** If the AI quality control fails, or if a backend service drops, the student must be informed, and state must not advance.
- **WHY it exists:** (PRD NFR-004) Pretending the system worked when a learning step failed ruins the curriculum progression.
- **WHAT the agent must do:** Implement transactional DB updates. Use try-catch blocks and explicit error states sent to the client.
- **WHAT happens if violated:** Execute Narrsistic Pluto RCA on the failure-handling logic.
- **EXAMPLE Violation:** Wrapping an AI generation call in a `try...except pass` block and returning a 200 OK while failing to actually update the user's progress.

## Constraint 9: Important learning decisions must be explainable
- **WHAT it means:** When the engine decides the user is "ready for the exam" or "weak in algebra," the reasoning must be logged and accessible.
- **WHY it exists:** (PRD NFR-008, FR-025) Opaque "black box" decisions cause user frustration and prevent tutors from understanding student paths.
- **WHAT the agent must do:** Store metadata, confidence scores, and historical traces for algorithmic decisions in the database.
- **WHAT happens if violated:** Design rejection. Halt task and expand scope to include explanation data structures.
- **EXAMPLE Violation:** Computing a final `exam_readiness_score = 0.85` as an aggregate without storing the individual topic mastery weights that produced it.

## Constraint 10: Provider-specific logic must not be embedded in core learning logic
- **WHAT it means:** No hardcoded OpenAI, Anthropic, or specific DB vendor logic in the core learning/domain services.
- **WHY it exists:** (PRD FR-023, NFR-007) To prevent vendor lock-in and allow hot-swapping of models.
- **WHAT the agent must do:** Use interfaces, adapter patterns, and dependency injection to abstract provider implementations.
- **WHAT happens if violated:** Refactor immediately to extract the dependency. Re-read ADR rules.
- **EXAMPLE Violation:** Importing the `openai` Python package directly inside `student_mastery_service.py` to calculate a score.
