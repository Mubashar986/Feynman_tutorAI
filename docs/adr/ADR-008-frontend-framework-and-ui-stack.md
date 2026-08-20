# ADR-008: Frontend Framework & UI Library Ecosystem

## 1. Context & Problem Statement
The platform requires a responsive, high-performance web interface supporting distraction-free timed exams, interactive LaTeX mathematical equation rendering, real-time Socratic tutor SSE streaming, and interactive node-link knowledge graphs (PRD §17, §27). The frontend must integrate seamlessly with FastAPI OpenAPI contracts, provide strict TypeScript type safety, maintain accessible UI components, and avoid unnecessary framework bloat.

## 2. Decision
Adopt **React 18+ with Vite and TypeScript (Strict Mode)** as the frontend framework, styled with **Tailwind CSS and Shadcn UI (Radix UI primitives)**, with specialized libraries for STEM and graph rendering:
* **LaTeX Formula Engine:** **KaTeX (`katex` + `react-katex`)** for zero-layout-shift mathematical and scientific formula rendering.
* **Knowledge & Misconception Maps:** **React Flow (`@xyflow/react`)** for interactive canvas rendering.
* **Server State Caching:** **TanStack Query v5 (React Query)** for query caching, deduplication, and optimistic updates.
* **Client UI State:** **Zustand** for lightweight local state (exam timer, active drawers, auth token hydration).
* **Icons:** **Lucide React**.

## 3. Evaluated Alternatives

### Option A: React + Vite + TypeScript + Shadcn UI + KaTeX + React Flow (Recommended)
* **Description:** Modern single-page client architecture with accessible Radix primitives and Tailwind tokens.
* **Pros:** Blazing fast Vite HMR, pure static SPA deployability (zero Node server runtime required in production), complete component ownership via Shadcn UI, industry standard KaTeX math rendering, flawless OpenAPI TypeScript integration.
* **Cons:** Client-side rendering only (acceptable since the entire learning app is behind authentication).
* **Mandatory Gates:** Passes all 10 gates.
* **Score:** 84/85.

### Option B: Next.js (App Router / SSR)
* **Description:** Full-stack React framework with Server-Side Rendering.
* **Pros:** Built-in SSR and routing.
* **Cons:** Adds unnecessary Node.js server operational complexity when FastAPI is already our backend API; server action abstractions conflict with pure OpenAPI contract-first generation; heavier bundle footprint.
* **Mandatory Gates:** Passes gates, but introduces architectural redundancy with FastAPI.
* **Score:** 62/85.

### Option C: Plain Vanilla React + Bootstrap / Material UI (MUI)
* **Description:** Traditional heavyweight component library.
* **Pros:** Familiar components out of the box.
* **Cons:** Heavy runtime CSS-in-JS overhead (MUI Emotion), opinionated styling difficult to customize for pedagogical focus mode, lacks native KaTeX and React Flow integration.
* **Mandatory Gates:** Passes gates, but poor design ergonomics.
* **Score:** 54/85.

## 4. Quality Control Matrix & Gate Evaluation

| Control | Option A (React + Vite + Shadcn) | Option B (Next.js SSR) | Option C (React + MUI) |
| :--- | :--- | :--- | :--- |
| **PRD Alignment** | 5 (Matches §17, §27) | 4 (Over-engineered backend) | 3 (Adequate) |
| **Performance (Client)** | 5 (Zero runtime CSS bloat) | 4 (Good) | 2 (Heavy CSS-in-JS runtime) |
| **Contract-First Fit** | 5 (Pure OpenAPI → TS types) | 3 (Conflicts with Server Actions) | 4 (Good) |
| **STEM / Math UX** | 5 (Native KaTeX integration)| 4 (Good) | 2 (Manual styling) |
| **Gate 1–10 Status** | **PASS (All 10)** | PASS | PASS |

## 5. Consequences & Implementation Blueprint
* `frontend/` directory configured with `vite.config.ts`, `tailwind.config.js`, `tsconfig.json`.
* Design system tokens defined in [docs/frontend_design/DESIGN_SYSTEM_TYPOGRAPHY.md](file:///c:/Users/Mubashar/Desktop/Curious_Feynman/docs/frontend_design/DESIGN_SYSTEM_TYPOGRAPHY.md).
* TypeScript contracts synced from FastAPI via `openapi-typescript`.

```yaml
adr_id: ADR-008
title: "Frontend Framework & UI Library Ecosystem"
decision_level: "Frontend Architecture / UI System"
status: accepted
date: "2026-08-20"
depends_on: [ADR-000]
supersedes: []
gates:
  - id: 6
    result: pass
    evidence: "Frontend respects server-side RBAC and enforces client route guards"
recommended_option: "Option A: React + Vite + TypeScript + Shadcn UI + KaTeX + React Flow"
priority_tier_used_for_tiebreak: "Tier 5 (Maintainability & Extensibility)"
open_assumptions: []
```
