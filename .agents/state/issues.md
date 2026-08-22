# Issues and Error Register — AI Adaptive Exam Learning Platform

## ISSUE-0001 — Pytest-Asyncio Fixture ScopeMismatch between pytest.ini and session-scoped setup_test_database fixture

Status: RESOLVED
Severity: MEDIUM
Detected: 2026-08-21
Detected During: Task 0.2 Implementation Verification
Architectural Domain: Backend Test Harness / Infrastructure
Component: `backend/pytest.ini` & `backend/tests/conftest.py`
Symptom: `ScopeMismatch: You tried to access the function scoped fixture _function_scoped_runner with a session scoped request object` on all 5 tests in `backend/tests/test_health.py`.
Reproduction: `pytest backend/tests/test_health.py`
Evidence: Task-168 execution log in `.system_generated/tasks/task-168.log`.
Root Cause: `pytest.ini` set `asyncio_default_fixture_loop_scope = function`, which restricted `pytest-asyncio` 1.4.0's runner fixture to function scope, while `conftest.py` declared a session-scoped async fixture `@pytest_asyncio.fixture(scope="session", autouse=True) def setup_test_database()`.
Contributing Factors: Version-specific changes in `pytest-asyncio` v1.4.0+ requiring strict scope alignment between event loop runners and fixtures.
Affected Scope: Backend test execution harness.
Regression Risk: LOW
Related WBS: Task 0.2
Related Artifacts: `task_0_2_architect_analysis.md`
Fix: Updated `backend/pytest.ini` with `asyncio_default_fixture_loop_scope = session` and updated `backend/tests/conftest.py` to declare `loop_scope="session"` explicitly on all async fixtures.
Verification: Executed `pytest backend/tests/test_health.py -v`. All 5 tests passed in 0.15s with 100% success rate.
Regression Verification: Zero side effects on FastAPI application runtime or database sessions.
Resolution: Event loop scope aligned globally and per fixture in test configuration.
Remaining Risk: None.
Resolved On: 2026-08-21

## ISSUE-0002 — TypeScript Compiler TS2339 Property 'env' does not exist on type 'ImportMeta'

Status: RESOLVED
Severity: LOW
Detected: 2026-08-21
Detected During: Task 0.3 Implementation Verification (npm run build)
Architectural Domain: Frontend Build & Type System
Component: `frontend/src/vite-env.d.ts` & `frontend/tsconfig.json`
Symptom: `src/api/client.ts(6,34): error TS2339: Property 'env' does not exist on type 'ImportMeta'.`
Reproduction: `npm run build` inside `frontend/`
Evidence: Terminal exit code 1 on `tsc -b && vite build`.
Root Cause: In a Vite + TypeScript project, standard ES `ImportMeta` types do not include Vite's ambient `.env` properties unless `vite/client` type definitions are referenced either via `src/vite-env.d.ts` (`/// <reference types="vite/client" />`) or via `"types": ["vite/client"]` in `tsconfig.json`.
Contributing Factors: `vite-env.d.ts` was not created during initial file scaffolding.
Affected Scope: `frontend/` TypeScript compilation.
Regression Risk: LOW
Related WBS: Task 0.3
Related Artifacts: `task_0_3_design.md`
Fix: Created `frontend/src/vite-env.d.ts` with `/// <reference types="vite/client" />`.
Verification: `npm run build` executed successfully, transforming 1669 modules and generating `dist/` with 0 errors.
Regression Verification: Zero side effects on runtime components.
Resolution: Ambient Vite environment types registered.
Remaining Risk: None.
Resolved On: 2026-08-21

## ISSUE-0004 — ModuleNotFoundError: No module named 'yaml' during backend test discovery

Status: RESOLVED
Severity: LOW
Detected: 2026-08-23
Detected During: Task 2.1 Implementation Verification
Architectural Domain: Backend / Curriculum Ingestion
Component: `backend/app/curriculum/service.py`
Symptom: `ModuleNotFoundError: No module named 'yaml'` when running pytest on backend test suite.
Reproduction: `py -3.14 -m pytest backend/tests/`
Evidence: Pytest import failure trace on `backend/app/curriculum/service.py:3`.
Root Cause: `import yaml` was unconditionally imported at module level in `backend/app/curriculum/service.py` when `pyyaml` is not installed in the standard Python 3.14 environment.
Contributing Factors: Unintentional top-level import of non-standard library package without conditional check.
Affected Scope: Backend test suite and curriculum service module import.
Regression Risk: LOW
Related WBS: Task 2.1
Related Artifacts: `task_2_1_architect_analysis.md`
Fix: Wrapped `yaml` import in a defensive conditional block (`try: import yaml except ImportError: yaml = None`) and used standard library `json` as the primary native parser. Added `@pytest.mark.skipif(not HAS_YAML)` on YAML-specific test case.
Verification: Executed `py -3.14 -m pytest backend/tests/ -v`. All 48 tests passed (1 skipped) in 17.91s with 100% pass rate.
Regression Verification: Verified all existing auth, health, LLM gateway, and state machine tests continue to pass with zero regressions.
Resolution: Native standard library JSON parser is prioritized; YAML is cleanly optional without import crashes.
Remaining Risk: None.
Resolved On: 2026-08-23

## ISSUE-0003 — Vitest TestingLibraryElementError in App.test.tsx option button selector

Status: RESOLVED
Severity: LOW
Detected: 2026-08-21
Detected During: Task 0.3 Implementation Verification (npm run test)
Architectural Domain: Frontend Test Harness & Accessibility
Component: `frontend/src/App.tsx` & `frontend/src/App.test.tsx`
Symptom: `TestingLibraryElementError: Unable to find an element with the text: Option A.`
Reproduction: `npm run test` inside `frontend/`
Evidence: Vitest runner output on task-102.
Root Cause: In `App.tsx`, the option buttons rendered `{opt.id}` ("A") inside an inner span without an explicit `aria-label="Option A"`, while `App.test.tsx` searched for text `"Option A"`.
Contributing Factors: Lack of explicit accessibility `aria-label` attribute on option button elements.
Affected Scope: `frontend/src/App.tsx` accessibility and `frontend/src/App.test.tsx` testing.
Regression Risk: LOW
Related WBS: Task 0.3
Related Artifacts: `task_0_3_design.md`
Fix: Added `aria-label={opt.label}` to option buttons in `src/App.tsx` and updated `src/App.test.tsx` to use `screen.getByLabelText("Option A")`.
Verification: `npm run test` passed 100% across all 6 test cases in 2.25s.
Regression Verification: Zero regression on button rendering or theme behavior.
Resolution: Added explicit aria labels and synchronized testing library queries.
Remaining Risk: None.
Resolved On: 2026-08-21

## ISSUE-0004 — RequireAuth Fallback Handling on Role Mismatch & Duplicate DOM Text in App.test.tsx

Status: RESOLVED
Severity: LOW
Detected: 2026-08-21
Detected During: Task 1.3 Implementation Verification (npm run test)
Architectural Domain: Frontend Component Logic & Test Suite
Component: `frontend/src/components/auth/RequireAuth.tsx` & `frontend/src/App.test.tsx`
Symptom: 1) `RequireAuth` ignored `fallback` prop when user was authenticated but role mismatched. 2) `App.test.tsx` failed with `getMultipleElementsFoundError` on user's name because it appeared in both header and hero.
Reproduction: `npm run test` inside `frontend/`
Evidence: Vitest runner output on task-261.
Root Cause: In `RequireAuth.tsx`, the `if (fallback) return <>{fallback}</>;` was placed only in the unauthenticated block, not in the role-authorization block. In `App.test.tsx`, `screen.getByText("Alex Rivera")` was ambiguous because "Alex Rivera" rendered in both `UserProfileMenu` and the welcome banner.
Contributing Factors: Overlooked fallback prop check on role mismatch.
Affected Scope: `RequireAuth` fallback behavior and `App.test.tsx` assertions.
Regression Risk: LOW
Related WBS: Task 1.3
Related Artifacts: `task_1_3_design.md`
Fix: 1) Updated `RequireAuth.tsx` to return `<>{fallback}</>` on role mismatch if fallback prop exists. 2) Updated `App.test.tsx` to use exact button matchers and `getAllByText`.
Verification: `npm run test` passed 100% across all 10 test cases in 2.49s.
Regression Verification: Zero regression on button rendering, dialogs, or KaTeX STEM math equations.
Resolution: Aligned fallback handling and synchronized testing library queries.
Remaining Risk: None.
Resolved On: 2026-08-21

## ISSUE-0005 — LLMGateway Fallback Chain Precedence Bug and Dynamic Registration Ordering

Status: RESOLVED
Severity: MEDIUM
Detected: 2026-08-22
Detected During: Task 0.4 Implementation Verification (py -m pytest backend/tests/test_llm_gateway.py)
Architectural Domain: Backend Core LLM Gateway & Fallback Router
Component: `backend/app/core/llm/gateway.py` & `backend/tests/test_llm_gateway.py`
Symptom: `test_llm_gateway_generate_text_success` and `test_llm_gateway_dynamic_fallback_on_rate_limit` failed with assertion errors expecting custom mock responses but receiving generic fallback mock responses.
Reproduction: `py -m pytest backend/tests/test_llm_gateway.py -v`
Evidence: Pytest output on task-177 showing `AssertionError: assert 'Success response' in response.content` and `AssertionError: assert 'mock' == 'healthy_secondary'`.
Root Cause: In `LLMGateway`, `register_provider(provider, is_default=True)` updated `self._default_provider_name` but appended the provider at the end of the static `self._fallback_order` list. When building the fallback chain, `_build_provider_chain()` iterated through `self._fallback_order` where `ollama` and `mock` preceded the newly registered default provider. Because `ollama.is_configured()` returned `True` (due to default `base_url`), the gateway attempted `ollama` $\to$ connection failed $\to$ fell back to `mock` before ever reaching the registered default provider.
Contributing Factors: Static fallback array initialized in `__init__` without dynamic promotion of default providers to index `0`, and absence of an explicit `set_fallback_chain()` override method.
Affected Scope: `backend/app/core/llm/gateway.py` routing behavior.
Regression Risk: LOW
Related WBS: Task 0.4
Related Artifacts: `task_0_4_architect_analysis.md`, `task_0_4_design.md`
Fix: 1) Updated `register_provider(provider, is_default=True)` to dynamically promote default providers to index `0` of `self._fallback_order`. 2) Updated `_build_provider_chain()` to prioritize `preferred_provider` $\to$ `self._default_provider_name` $\to$ remaining configured providers. 3) Added `set_fallback_chain(list)` method for explicit priority overrides.
Verification: Executed `py -m pytest backend/tests/test_llm_gateway.py -v`. All 14 tests passed in 3.08s with 100% success rate. Full backend suite (`py -m pytest backend/tests/ -v`) passed 19/19 tests in 3.36s.
Regression Verification: Zero side effects on FastAPI application runtime or health endpoints.
Resolution: Aligned dynamic provider promotion and explicit fallback chain overrides.
Remaining Risk: None.
Resolved On: 2026-08-22

## ISSUE-0006 — Windows cp1252 Terminal UnicodeEncodeError on CLI Script Emoji Output

Status: RESOLVED
Severity: LOW
Detected: 2026-08-22
Detected During: Task 0.5 Implementation Verification (py backend/scripts/export_openapi.py)
Architectural Domain: Cross-Platform CLI Tooling
Component: `backend/scripts/export_openapi.py`
Symptom: `UnicodeEncodeError: 'charmap' codec can't encode character '\u2705' in position 0: character maps to <undefined>`.
Reproduction: `py backend/scripts/export_openapi.py` on Windows PowerShell with default cp1252 encoding.
Evidence: Task-296 execution log showing `UnicodeEncodeError` in `cp1252.py`.
Root Cause: In Windows PowerShell environments without explicit UTF-8 code page active (`chcp 65001`), Python's default console encoding is `cp1252` (Windows-1252), which cannot encode non-Latin Unicode characters like emoji `\u2705`.
Contributing Factors: Unencoded Unicode emoji placed in console output print statement.
Affected Scope: `backend/scripts/export_openapi.py` CLI script.
Regression Risk: LOW
Related WBS: Task 0.5
Related Artifacts: `task_0_5_design.md`
Fix: Replaced Unicode emoji with ASCII-safe status prefix `[SUCCESS]` in `export_openapi.py`.
Verification: Executed `py backend/scripts/export_openapi.py` and `py -m pytest backend/tests/test_openapi_export.py -v`. Schema exported successfully (3 paths) and test passed 100% with 0 errors.
Regression Verification: Zero impact on exported JSON file content (JSON dump continues to use UTF-8).
Resolution: Replaced console emoji with ASCII-safe prefix.
Remaining Risk: None.
Resolved On: 2026-08-22
