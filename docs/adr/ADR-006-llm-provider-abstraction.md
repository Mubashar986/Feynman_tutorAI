# ADR-006: Multi-Provider LLM Gateway & Structured Output Validation Engine

## 1. Context & Problem Statement
The platform relies heavily on Large Language Models for question generation, distractor reasoning, Socratic tutoring, rubric grading, and misconception analysis (PRD §14, §27, FR-004, FR-008, FR-010, FR-023). However:
1. Hardcoding any single provider (e.g. OpenAI or Anthropic) violates PRD FR-023 and Non-Negotiable Constraint #10.
2. Raw LLM output must **never** directly become canonical learning state (PRD Constraint #1).
3. Different tasks require different model tiers: complex question generation requires heavy reasoning models (Claude 3.5 Sonnet / GPT-4o / Gemini 1.5 Pro), real-time Socratic chat requires ultra-low latency models (Gemini 1.5 Flash / Claude 3.5 Haiku / GPT-4o-mini), and offline dev/testing requires local models (Ollama / Llama 3.1).
4. Provider outages or rate limits must not bring down the platform.

## 2. Decision
Implement an async **Multi-Provider LLM Gateway Protocol (`LLMGatewayBase`)** with concrete adapters for **Google Gemini, OpenAI, Anthropic, and local Ollama**, coupled with strict **Pydantic V2 Schema Validation** for all structured outputs.
* **Tier 1 (High Reasoning):** Claude 3.5 Sonnet / GPT-4o / Gemini 1.5 Pro (used for Question Lab, Blueprint Extraction, and Teach-Back Rubric Grading).
* **Tier 2 (Fast Interactive):** Gemini 1.5 Flash / Claude 3.5 Haiku / GPT-4o-mini (used for Real-time Socratic Tutor Streaming and Fast Classifications).
* **Tier 3 (Local / Free):** Ollama Llama 3.1 / Qwen 2.5 (used for offline development and local test suites).
* **Dynamic Fallback:** If Tier 1/2 primary provider fails or hits a rate limit (HTTP 429), the gateway automatically retries the request with a secondary provider.

## 3. Evaluated Alternatives

### Option A: Custom Async Multi-Provider Gateway + Pydantic V2 (Recommended)
* **Description:** Clean Python abstract protocol (`LLMProviderBase`) with provider adapters and strict Pydantic V2 response parsing.
* **Pros:** 100% vendor independent (PRD FR-023), zero bloated framework overhead, strict Pydantic schema validation before any data touches domain logic, dynamic retry/fallback, full testability with mocked provider fixtures.
* **Cons:** Requires maintaining provider adapter implementations.
* **Mandatory Gates:** Passes all 10 gates.
* **Score:** 85/85 (Perfect alignment with PRD §27 & FR-023).

### Option B: LangChain / LlamaIndex Heavy Framework
* **Description:** Use all-in-one AI agent framework.
* **Pros:** Pre-built ecosystem.
* **Cons:** Rapidly changing abstractions, unnecessary complexity, difficult to debug streaming SSE internals, hidden prompts and opinionated state mutations that violate PRD Constraint #1.
* **Mandatory Gates:** Fails Gate 1 & 3 due to hidden state side-effects.
* **Score:** 45/85.

### Option C: Hardcoded Single Provider SDK (e.g. OpenAI only)
* **Description:** Directly import `openai` SDK in tutor and assessment services.
* **Pros:** Quickest initial implementation.
* **Cons:** Directly violates PRD Constraint #10 ("Provider-specific logic must not be embedded in core learning logic") and PRD §3.2.
* **Mandatory Gates:** FAILS GATE 10 OUTRIGHT.
* **Score:** 20/85 (Forbidden anti-pattern).

## 4. Quality Control Matrix & Gate Evaluation

| Control | Option A (Custom Gateway) | Option B (LangChain) | Option C (Direct SDK) |
| :--- | :--- | :--- | :--- |
| **PRD Alignment** | 5 (Matches FR-023, §27) | 3 (Over-abstracted) | 1 (Violates FR-023) |
| **AI Safety & Validation**| 5 (Pydantic schema gate) | 3 (Framework defaults) | 2 (Manual JSON parsing) |
| **Maintainability** | 5 (Clean protocol) | 2 (Breaking upstream changes) | 2 (Vendor lock-in) |
| **Gate 1–10 Status** | **PASS (All 10)** | FAIL | **FAIL (Gate 10)** |

## 5. Consequences & Implementation Blueprint
* `LLMProviderBase` abstract class created in `backend/app/core/llm/base.py`.
* Concrete adapters in `backend/app/core/llm/providers/` (`gemini.py`, `openai.py`, `anthropic.py`, `ollama.py`).
* `LLMGateway` handles model routing, fallback retries, and Pydantic validation in `backend/app/core/llm/gateway.py`.

```yaml
adr_id: ADR-006
title: "Multi-Provider LLM Gateway & Structured Output Validation Engine"
decision_level: "AI Architecture / Core Abstraction"
status: accepted
date: "2026-08-20"
depends_on: [ADR-000]
supersedes: []
gates:
  - id: 1
    result: pass
    evidence: "Strict Pydantic V2 validation ensures raw LLM text is never stored directly as learning state"
  - id: 4
    result: pass
    evidence: "Generated assessment items are validated against Pydantic schemas before persistence"
  - id: 10
    result: pass
    evidence: "All provider logic is isolated behind LLMProviderBase protocol"
recommended_option: "Option A: Custom Async Multi-Provider Gateway + Pydantic V2"
priority_tier_used_for_tiebreak: "Tier 1 (AI Safety & Non-Negotiable Gate 10)"
open_assumptions: []
```
