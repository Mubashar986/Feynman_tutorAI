# Frontend Developer Track Guide
## AI Adaptive Exam Learning Platform

This guide outlines the responsibilities, tech stack, and protocols for the Frontend Developer track.

### 1. Frontend Stack Foundation
The frontend track focuses on building a highly interactive, accessible, and type-safe user interface.
- **Framework:** React (via Vite or Next.js — pending FDR-001)
- **Language:** TypeScript (strict mode enabled)
- **Styling:** Tailwind CSS + component library (e.g., shadcn/ui or Radix UI)
- **Data Fetching:** TanStack Query (React Query) or similar
- **State Management:** Zustand, Jotai, or React Context (pending FDR-003)
- **API Client:** Generated from OpenAPI specs

### 2. Frontend Directory Structure
The frontend codebase follows a feature-based architecture to maintain scalability.

```text
frontend/
├── src/
│   ├── api/            # Generated API clients and types
│   ├── assets/         # Static assets (images, fonts)
│   ├── components/     # Reusable, generic UI components (buttons, inputs)
│   ├── features/       # Feature-specific modules (e.g., exams, dashboards)
│   │   └── exam-player/
│   │       ├── components/
│   │       ├── hooks/
│   │       └── api.ts
│   ├── hooks/          # Global custom hooks
│   ├── layouts/        # Page layout wrappers
│   ├── pages/          # Route components
│   ├── store/          # Global state management
│   ├── styles/         # Global CSS and Tailwind configs
│   ├── types/          # Global TypeScript definitions
│   └── utils/          # Helper functions
├── mocks/              # MSW handlers and mock data fixtures
└── package.json / tsconfig.json
```

### 3. Frontend Stage Lifecycle Adaptations
When applying the project's stage-gated lifecycle to frontend tasks:
- **Stage 0 (WBS):** Break the screen down into atomic components, identify necessary hooks, and define required API queries.
- **Stage 1 (Conceptual):** Map out the UI state machine (e.g., `Idle` → `Loading` → `Streaming` → `Success` or `Error`). Establish physical analogies for UI patterns to ensure intuitive design.
- **Pluto (RCA):** Evaluate bundle size impacts, identify potential unnecessary re-render patterns, and analyze SSR vs. CSR trade-offs before implementation.
- **Stage 2 (Design):** Define component hierarchy, establish strict interface definitions for props using Zod schemas if necessary, and define the shape of mock data.
- **Stage 3 (Implementation):** Build the components. Understand the browser event loop, CSS layout algorithms (Flexbox/Grid), DOM accessibility requirements, and the internals of complex renderers (like LaTeX or Mermaid). Write clean, type-safe React code.
- **Stage 4 (Validation):** Perform visual regression tests, responsive design checks, verify keyboard navigation and screen reader compatibility, and ensure error boundaries catch unexpected failures gracefully.

### 4. Frontend Error Lock
The frontend workflow enforces a strict "Error Lock" mechanism. Any of the following triggers an immediate halt and requires a Pluto (Root Cause Analysis) phase:
- `npm run build` failures (e.g., Vite build errors).
- `tsc --noEmit` type errors.
- Vitest/Jest test suite failures.
- Unhandled runtime React errors caught during development.

### 5. Consuming API Contracts
The frontend track relies entirely on Contract-First Development:
1. Obtain the updated OpenAPI schema from the backend (`docs/contracts/schemas/`).
2. Run the type generation script (e.g., `openapi-typescript`) to create strict TypeScript types.
3. Configure MSW (Mock Service Worker) using these generated types to simulate API responses during development.
4. Build the UI against the mocked data.
5. Once the backend endpoint is verified live, disable MSW and connect to the real service.

### 6. Zero-Silent-Deps Examples
Do not mindlessly add familiar libraries without evaluation. For example:
- **Don't default to Axios:** Evaluate native `fetch` vs. `ky` vs. `axios`.
- **Don't default to Redux:** Evaluate `TanStack Query` + `Zustand` vs. `Jotai` vs. `React Context`.
- **Don't default to styled-components:** Evaluate Tailwind CSS + generic unstyled components (Radix) vs. full component libraries (Mantine).

### 7. Accessibility & Performance Guidelines
- **Accessibility (A11y):** All interactive elements must be keyboard navigable. Provide ARIA labels where semantic HTML is insufficient. Ensure sufficient color contrast.
- **Performance:** Monitor bundle size. Implement code splitting for large routes or heavy libraries (like LaTeX renderers). Avoid unnecessary re-renders by properly using memoization (`useMemo`, `useCallback`) where appropriate.

### 8. Relevant Decision Registries
As a frontend developer, you must actively manage and consult:
- **FDR-INDEX.md:** For all frontend architecture, framework, styling, and state management decisions.
- **CONTRACT-PROTOCOL.md:** To ensure strict adherence to API synchronization.
