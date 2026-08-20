# ADR-000: MVP Capability Slice — Phase 1 Boundary vs. Subsequent Milestones

## 1. Context & Problem Statement
The PRD defines 20 major product capabilities for the AI-Powered Adaptive Exam Learning Platform. Building all 20 capabilities at once introduces high architectural complexity, severe delivery risk, and makes rigorous quality gating unmanageable. We must define a strict, coherent vertical slice for Phase 1 (MVP) that delivers a complete, demonstrable learning loop without sacrificing architectural integrity or non-negotiable constraints.

## 2. Decision
Adopt a 3-Phase Milestone delivery boundary:
* **Phase 1 (Core MVP Slice):**
  * Exam Template Engine (Cap 2)
  * Student Mastery Model & Isolated State Machine (Cap 3, PRD §13)
  * Question Laboratory & Strict Schema Assessment Engine (Cap 4, 15)
  * Resource / Past Paper Ingestion & Hybrid RAG Retrieval (Cap 5, 8)
  * Source-Grounded Socratic AI Tutor with SSE Streaming (Cap 8, 10)
  * Error Bank & Misconception Log (Cap 6)
  * Distraction-Free Exam Player & KaTeX Formula Rendering (§17)
* **Phase 2 (Adaptive Revision & Deep Learning Modes):**
  * Spaced Repetition Revision Scheduling (Cap 7)
  * Teach-Back Mode & Rubric Evaluator (Cap 17)
  * Adversarial Tutor & Why-You-Are-Wrong Modes (Cap 18, 19)
  * Interactive Misconception DAG Visualizer with React Flow (Cap 12, 13)
* **Phase 3 (Simulation & Advanced Intelligence):**
  * Exam Readiness Simulator (Cap 9, 20)
  * Exam Blueprint Reverse Engineering (Cap 14)
  * Multimodal Generation (Cap 16)
  * Personal Learning Twin (Cap 11)

## 3. Evaluated Alternatives

### Option A: All 20 Capabilities in Single Milestone
* **Description:** Attempt to implement all 20 PRD capabilities simultaneously before releasing a baseline.
* **Pros:** Complete PRD coverage from day one.
* **Cons:** Massive blast radius, unmanageable test surface, delayed feedback loop, high failure risk.
* **Mandatory Gates:** Fails Gate 4 & 5 during early dev due to incomplete validation scaffolding.
* **Score:** 18/85 (Fails MVP Fit, Maintainability, Risk).

### Option B: 3-Phase Milestone Structure (Recommended)
* **Description:** Build the closed core loop (Template → Syllabus → Ingestion → Assessment → Mastery → Grounded Tutor → Error Bank) first in Phase 1, then expand.
* **Pros:** Closes the central product loop (Exam → Curriculum → Student Model → Assessment → Diagnosis → Repair), enables immediate end-to-end testing, fully satisfies all 10 mandatory gates.
* **Cons:** Postpones advanced modes (Teach-back, Adversarial) to Phase 2.
* **Mandatory Gates:** Passes all 10 gates.
* **Score:** 82/85.

### Option C: Barebones Chatbot MVP
* **Description:** Build a simple RAG chatbot with an exam prompt.
* **Pros:** Fast to hack together.
* **Cons:** Violates PRD §2.3 ("Platform must not be designed as User → Chat Interface → LLM → Answer") and violates Gate 1, 2, 3.
* **Mandatory Gates:** Fails Gates 1, 2, 3, 4.
* **Score:** 15/85 (Actively forbidden).

## 4. Quality Control Matrix & Gate Evaluation

| Control | Option A (All-in-One) | Option B (3-Phase Slice) | Option C (Chatbot) |
| :--- | :--- | :--- | :--- |
| **PRD Alignment** | 4 (Complete scope) | 5 (Follows §1, §3.1) | 1 (Violates §2.3) |
| **Correctness & Safety** | 2 (Overwhelming bugs) | 5 (Iterative verification) | 1 (Unguarded LLM) |
| **MVP Fit** | 1 (Too large) | 5 (Optimal closed loop) | 2 (Not an adaptive platform) |
| **Implementation Effort**| 1 (Extreme) | 4 (Manageable) | 5 (Trivial) |
| **Gate 1–10 Status** | FAIL | **PASS (All 10)** | FAIL |

## 5. Consequences & Implementation Blueprint
* Phase 1 focuses strictly on Epics 0 through 6.
* WBS tasks for Epics 7 and 8 are scheduled under Phase 2 and Phase 3 without blocking core scaffolding.
* All Phase 1 modules must establish clean extension points for Phase 2/3 features.

```yaml
adr_id: ADR-000
title: "MVP Capability Slice — Phase 1 Boundary vs. Subsequent Milestones"
decision_level: "Product / Architectural Governance"
status: accepted
date: "2026-08-20"
depends_on: []
supersedes: []
gates:
  - id: 1
    result: pass
    evidence: "Phase 1 implements state machine and mastery engine isolating LLM from official learning state"
  - id: 2
    result: pass
    evidence: "Phase 1 requires per-student isolated learning state schema"
  - id: 3
    result: pass
    evidence: "Phase 1 includes auditable state transition logging (PRD §13)"
  - id: 4
    result: pass
    evidence: "Phase 1 requires pre-deployment question validation"
  - id: 5
    result: pass
    evidence: "Phase 1 requires RAG retrieval before Socratic tutor generation"
  - id: 6
    result: pass
    evidence: "Phase 1 enforces server-side RBAC"
  - id: 7
    result: pass
    evidence: "Phase 1 implements untrusted file validation"
  - id: 8
    result: pass
    evidence: "Phase 1 blocks student progression on critical mastery failure"
  - id: 9
    result: pass
    evidence: "Phase 1 mastery and error logs are explainable"
  - id: 10
    result: pass
    evidence: "Phase 1 abstracts LLM behind multi-provider gateway"
recommended_option: "Option B: 3-Phase Milestone Structure"
priority_tier_used_for_tiebreak: "Tier 4 (PRD Alignment / MVP Fit)"
open_assumptions: []
```
