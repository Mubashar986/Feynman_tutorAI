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
Evidence: Pytest import failure trace on `backend/app/curriculum/service.py:1`.
Root Cause: `import yaml` (PyYAML) was imported unconditionally for syllabus parsing, but PyYAML is not installed in the standard Python 3.14 environment.
Contributing Factors: Third-party library import without platform/standard library fallback evaluation.
Affected Scope: `backend/app/curriculum/service.py`.
Regression Risk: LOW
Related WBS: Task 2.1
Related Artifacts: `task_2_1_design.md`
Fix: Replaced `import yaml` with a robust native syllabus parser utilizing standard library `json` and regex frontmatter parsing.
Verification: `py -3.14 -m pytest backend/tests/ -v` passed with 100% pass rate.
Regression Verification: Zero side effects on curriculum models or syllabus ingestion.
Resolution: Replaced third-party PyYAML with native Python standard library parsers.
Remaining Risk: None.
Resolved On: 2026-08-23

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
Verification: `py backend/scripts/export_openapi.py` generated `docs/contracts/schemas/openapi.json` without encoding errors.
Regression Verification: Zero side effects on contract export.
Resolution: Emoji replaced with ASCII text.
Remaining Risk: None.
Resolved On: 2026-08-22

## ISSUE-0007 — ModuleNotFoundError: No module named 'aiofiles' during test collection

Status: RESOLVED
Severity: LOW
Detected: 2026-08-23
Detected During: Task 3.1 Implementation Verification
Architectural Domain: Backend / Storage
Component: `backend/app/core/storage/local.py`
Symptom: `ModuleNotFoundError: No module named 'aiofiles'` when running pytest on backend test suite.
Reproduction: `py -3.14 -m pytest backend/tests/`
Evidence: Pytest import failure trace on `backend/app/core/storage/local.py:5`.
Root Cause: `import aiofiles` was used for file I/O when `aiofiles` is not installed in the standard Python 3.14 environment.
Contributing Factors: Unintentional import of third-party library when native standard library `asyncio.to_thread` with built-in `open` / `Path` provides non-blocking, zero-dependency async file I/O natively.
Affected Scope: `backend/app/core/storage/local.py`.
Regression Risk: LOW
Related WBS: Task 3.1
Related Artifacts: `task_3_1_design.md`
Fix: Replaced `aiofiles` with standard library `asyncio.to_thread` and native `Path.write_bytes` / `Path.read_bytes` / `os.remove`.
Verification: `py -3.14 -m pytest backend/tests/ -v` passed with 100% pass rate.
Regression Verification: Zero side effects on storage sandbox or file saving.
Resolution: Replaced third-party `aiofiles` with standard library primitives.
Remaining Risk: None.
Resolved On: 2026-08-23

## ISSUE-0008 — Teach-Back API Endpoint HTTP 500 Due to Unmocked LLMGateway In Test & GroundedRetrievalService Method Name Mismatch

Status: RESOLVED
Severity: MEDIUM
Detected: 2026-08-23
Detected During: Task 7.2 Stage 4 Testing Verification
Architectural Domain: Backend / Teach-Back Mode & AI Layer
Component: `backend/app/teach_back/service.py` & `backend/tests/test_teach_back.py`
Symptom: `POST /api/v1/teach-back/evaluate` returned `500 Internal Server Error` in API integration test `test_teach_back_full_api_suite_and_isolation`.
Reproduction: `py -3.14 -m pytest backend/tests/test_teach_back.py -v`
Evidence: Test task-159 log showing fallback to unconfigured Ollama -> default `MockLLMProvider` generic dict failing `TeachBackLLMEvaluationOutput` Pydantic validation.
Root Cause: 
1. In `TeachBackService.evaluate_explanation()`, `GroundedRetrievalService.retrieve_relevant_chunks` was referenced instead of `GroundedRetrievalService.search_curriculum_sources`.
2. In `test_teach_back_full_api_suite_and_isolation`, `LLMGateway.generate_structured` was not monkeypatched with deterministic test evaluation data, so the default gateway initialization attempted an unconfigured network provider before falling back to a generic unshaped mock dict.
Contributing Factors: API test did not isolate the external LLM provider interface via standard `monkeypatch.setattr`.
Affected Scope: `backend/app/teach_back/service.py` and `backend/tests/test_teach_back.py`.
Regression Risk: LOW
Related WBS: Task 7.2
Related Artifacts: `task_7_2_design.md`
Fix: 
1. Updated `GroundedRetrievalService.search_curriculum_sources` call in `TeachBackService.evaluate_explanation`.
2. Added `monkeypatch.setattr(LLMGateway, "generate_structured", mock_generate_structured)` in API test.
Verification: Executed `py -3.14 -m pytest backend/tests/test_teach_back.py -v`. All 7 tests passed with 100% success rate. Full backend suite (`py -3.14 -m pytest backend/tests/ -v`) passed 115/115 tests in 43.62s.
Regression Verification: Zero side effects on other tutor, revision, or question bank services.
Resolution: Aligned RAG retrieval method and added deterministic mock provider monkeypatch in API integration test.
Remaining Risk: None.
Resolved On: 2026-08-23
