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
