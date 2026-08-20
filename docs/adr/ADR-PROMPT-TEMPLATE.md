# Enhanced ADR Generation Prompt — AI-Powered Adaptive Exam Learning Platform

This is a decision-driven, quality-gated architecture prompt. Use it once per
architectural decision. Store every output under `/docs/adr/ADR-<id>-<slug>.md`.
Maintain `/docs/adr/ADR-INDEX.md` listing id, title, status, and dependencies.

---

## ROLE

You are a Senior Solutions Architect, AI Systems Architect, and Education
Platform Engineer producing a formal Architecture Decision Record (ADR).

---

## 1. INPUTS (fill in every time)

| Field | Value |
|---|---|
| Decision | `[INSERT DECISION HERE]` |
| Decision level | Product / System / Container / Component / Relationship / Domain / Data / API / AI / Operational / Quality |
| Related artifact(s) | `[INSERT ARTIFACT / PRD SECTION / DIAGRAM]` |
| PRD/SRS version | `[version or commit hash]` |
| Scale & scope assumptions (MVP boundary) | e.g. "single-institution pilot, <2,000 concurrent students, one exam type, English only" |
| Regulatory context | e.g. FERPA / GDPR / none specified — **if none specified, this must be flagged as an open question, not assumed** |
| Prior accepted ADRs this decision must stay consistent with | `[ADR-IDs]` or "none" |

---

## 2. SYSTEM-WIDE NON-NEGOTIABLE CONTEXT

- The LLM is a component, not the authoritative system.
- Student learning state must be isolated per student and exam, auditable, and protected.
- The system must avoid vendor lock-in.
- The goal is a Minimum Viable Quality Product — bounded by the scope assumptions above, not "as robust as possible."
- **Any constraint not explicitly present in the PRD/SRS must be stated as an assumption, not silently treated as fact.**
- **If this decision conflicts with a previously accepted ADR, the conflict must be surfaced explicitly, not silently resolved.**

---

## 3. PRIORITY ORDER (used to break ties between options — fixed, do not reorder per-decision)

1. AI safety / Security / Privacy — non-negotiable floor
2. Correctness / Data integrity / Reliability
3. Auditability / Explainability
4. PRD alignment / MVP fit
5. Maintainability / Extensibility
6. Scalability / Performance
7. Cost / Implementation effort

When two options are close on total score, the recommendation must state
*which tier* broke the tie. "Higher total score" alone is not an acceptable
justification.

---

## 4. SCORING RUBRIC (anchors — every score must map to one of these, not be assigned freely)

| Score | Meaning |
|---|---|
| 1 | Fails outright / violates a mandatory gate / actively unsafe |
| 2 | Weak — workable only with major rework |
| 3 | Adequate — meets the stated PRD requirement, nothing more |
| 4 | Strong — meets the requirement with margin, some evidence |
| 5 | Excellent — evidenced, exceeds the requirement without overengineering |

**Rule:** every 1–5 score must carry a one-line justification citing either a
PRD/SRS section or an explicitly stated assumption. A bare number is not a
valid score.

---

## 5. QUALITY CONTROLS (score 1–5 each, with justification)

1. PRD alignment
2. Correctness
3. Security
4. Privacy
5. Maintainability
6. Scalability
7. Performance
8. Reliability
9. Data integrity
10. Explainability
11. Auditability
12. Extensibility
13. AI safety
14. MVP fit
15. Cost
16. Implementation effort
17. Risk

---

## 6. MANDATORY GATES (pass/fail — no partial credit)

1. LLM output must not directly become official learning state.
2. Student state must be isolated per student and exam.
3. Learning-state transitions must be valid and auditable.
4. Generated questions must be validated before student use.
5. Source-grounded answers must use retrieval before generation.
6. Role-based access must be enforced server-side.
7. Uploaded files must be treated as untrusted.
8. The system must not silently advance a student after critical failure.
9. Important decisions must be explainable.
10. Provider-specific logic must not be embedded in core learning logic.
11. **Any option that fails a gate is automatically ineligible for recommendation — regardless of total quality score.**
12. **Assumptions used to justify a gate pass must be listed explicitly, not implied.**
13. **If the option invalidates a previously accepted ADR, that ADR must be marked "requires supersession" — never silently overridden.**

---

## 7. REQUIRED OUTPUT PER OPTION (five options minimum)

1. Option name
2. Short description
3. How it works
4. PRD/SRS traceability — exact requirement IDs/sections relied on, or "no direct requirement — assumption: `[stated]`"
5. Pros
6. Cons
7. Risks
8. Mandatory gate table: gate # → pass/fail → **verification method** (unit test / integration test / manual review checklist / static analysis rule)
9. Quality score 1–5 for all 17 controls, each with a one-line justification
10. MVP suitability
11. Long-term suitability
12. Reversibility — cost/effort to undo this choice later if it proves wrong

---

## 8. REQUIRED FINAL OUTPUT

1. Comparison table (all options × all quality controls + gate pass/fail)
2. Recommended option
3. Why recommended — must cite the priority order (Section 3), not just "highest score"
4. Why the others were rejected — must cite either a failed gate or a specific lower-priority-tier weakness
5. Consequences of the recommendation
6. Implementation notes
7. Rollback plan for the recommendation
8. Consistency check against prior ADRs (which were checked, any requiring supersession)
9. Open risks
10. Follow-up decisions
11. Machine-readable summary block (see below)

---

## 9. MACHINE-READABLE SUMMARY BLOCK (append to every ADR)

```yaml
adr_id: ADR-XXX
title: ""
decision_level: ""
status: proposed        # proposed | accepted | superseded
date: ""
depends_on: []
supersedes: []
gates:
  - id: 1
    result: pass        # pass | fail
    evidence: ""
recommended_option: ""
priority_tier_used_for_tiebreak: ""
open_assumptions: []
```

This block lets the decision registry (and eventually CI tooling) check
compliance programmatically instead of relying on someone re-reading prose.

---

## 10. COMPANION RULE FOR THE CODING AGENT (this is the piece that actually stops "random" implementation choices)

This is **not** part of the per-decision prompt — it's a standing instruction
you give your agentic coding platform (Claude Code or equivalent) once, at
the project level:

> Before writing or modifying code for any component, check `/docs/adr/` for
> an accepted ADR governing that component. If one exists, restate its
> applicable gates and constraints as a checklist before writing any code,
> and verify the implementation against that checklist before marking the
> task complete.
>
> If no ADR exists for a decision the code requires (e.g. caching strategy,
> retry policy, state schema, error-handling behavior), do not choose
> silently. Either (a) stop and request an ADR be generated using the ADR
> prompt, or (b) create a lightweight "implementation-time ADR stub"
> recording the choice made and its rationale, so it can be reviewed later.

Without this, the ADR is a document the coding agent never re-reads — it's
architecture theater. With it, the ADR becomes a gate the agent has to pass
through before it's allowed to improvise.

---

## 11. ANTI-PATTERNS — forbidden regardless of quality score

- Storing raw LLM output as canonical learning state
- Trusting client-supplied role/permission flags
- Serving generated questions without a validation step
- Embedding provider-specific SDK calls inside core domain/learning logic
- Treating uploaded file content as executable or trusted input
- Silent retries or advancement past a critical failure state
