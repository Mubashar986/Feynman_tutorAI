# Narrsistic Pluto — Principal Architect & QA/SRE RCA Report
## Task 0.2 Defect RCA: Pytest-Asyncio Fixture Scope Mismatch

**Document Version:** 1.0  
**Classification:** Operational Defect / Test Harness Scope Conflict (ISSUE-0001)  
**Risk Profile:** Low  
**Confidence:** High — Directly traced in `backend/pytest.ini` and `backend/tests/conftest.py` with `pytest-asyncio` 1.4.0 runtime output  
**Target:** `backend/pytest.ini`, `backend/tests/conftest.py`

---

### 0. Task Intake & Definition of Ready
* **Acceptance Criteria:** `pytest backend/tests/test_health.py` must execute all 5 unit and integration tests successfully with zero errors, zero warnings, and clean session teardown.
* **Assumptions Ledger:**
  * Tests run against isolated in-memory SQLite (`sqlite+aiosqlite:///:memory:`).
  * `pytest-asyncio` version installed is 1.4.0+.

---

### 1. Architectural Compliance & Codebase Topology
* **Prescriptive Model Alignment:** The test harness must provide non-leaking, isolated async transactions for every individual test function without re-creating the entire engine metadata on every single test.
* **Blast Radius:** Internal test infrastructure only (`backend/pytest.ini`, `backend/tests/conftest.py`).
* **Semver Classification:** PATCH (internal test configuration).
* **Breaking Change Risk:** Low.

---

### 2. Defect Diagnostics & Root Cause Analysis (RCA)

#### Fault Activation Chain
1. User/Agent runs `pytest backend/tests/test_health.py`.
2. Pytest loads `backend/pytest.ini`, reading `asyncio_default_fixture_loop_scope = function`.
3. Pytest discovers session-scoped fixture `@pytest_asyncio.fixture(scope="session", autouse=True) def setup_test_database()`.
4. Pytest evaluates the fixture dependency tree: the session-scoped fixture attempts to request the async runner fixture `_scoped_runner`.
5. Because `pytest.ini` pinned fixture runner scope to `function`, pytest raises `ScopeMismatch: You tried to access the function scoped fixture _function_scoped_runner with a session scoped request object`.
6. All 5 collected test cases crash during setup before executing a single assertion.

#### 5-Whys Root Cause Analysis
1. *Why did the test suite fail?* Pytest raised a `ScopeMismatch` error during fixture setup.
2. *Why did ScopeMismatch occur?* A session-scoped fixture requested a function-scoped async event loop runner fixture.
3. *Why was the runner fixture function-scoped?* `pytest.ini` explicitly declared `asyncio_default_fixture_loop_scope = function`.
4. *Why did we declare `asyncio_default_fixture_loop_scope = function`?* To match standard individual test function isolation, without realizing `setup_test_database` was session-scoped.
5. *Root Cause:* Scope mismatch between global pytest configuration (`asyncio_default_fixture_loop_scope = function`) and async fixture scope (`scope="session"`).

* **Severity:** Sev3 (Blocks test execution, zero production impact).

---

### 3. Alternative Engineering Solutions (Web-Researched)

#### Approach 1: Align Global Loop Scope to Session in `pytest.ini` (Recommended)
* **Implementation Blueprint:** Set `asyncio_default_fixture_loop_scope = session` and `asyncio_default_test_loop_scope = function` in `pytest.ini`.
* **Sources Consulted:** Official `pytest-asyncio` v1.4.0+ documentation & GitHub issue trackers on scoped runners.
* **Pros:** Allows session-scoped database table setup while maintaining isolated function-scoped test transactions.
* **Cons:** Requires tests to manage transaction rollbacks cleanly per function.
* **Why might be rejected:** None; standard idiom.

#### Approach 2: Make `setup_test_database` Function-Scoped
* **Implementation Blueprint:** Change `@pytest_asyncio.fixture(scope="function", autouse=True)` in `conftest.py`.
* **Pros:** Simplifies scope to pure function level.
* **Cons:** Runs `create_all` and `drop_all` on every single test function, adding ~50ms overhead per test across a large test suite.
* **Why might be rejected:** Unnecessary table creation churn as test count scales to hundreds.

#### Approach 3: Use Explicit `loop_scope="session"` on the Fixture Definition
* **Implementation Blueprint:** Keep `pytest.ini` default and add `@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)` to `conftest.py`.
* **Pros:** Precise per-fixture scope control.
* **Cons:** Requires verbosity on every async fixture declaration.
* **Why might be rejected:** Minor verbosity.

---

### 4. Comparative Matrix

| Approach | Complexity | Perf / Overhead | Test Isolation | Rollout Risk | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Approach 1 (Global Session Loop)** | Low | High (Fast) | High (Transaction rollback) | Low | **RECOMMENDED** |
| **Approach 2 (Pure Function Scope)** | Low | Medium (Churn) | High | Low | Alternative |
| **Approach 3 (Explicit loop_scope)** | Low | High | High | Low | Viable |

---

### 5. Principal Recommendation
Apply **Approach 1 & Approach 3 combined**: Update `backend/pytest.ini` with `asyncio_default_fixture_loop_scope = session` and ensure `backend/tests/conftest.py` declares function-scoped transactional fixtures (`db_session`, `async_client`) with clean per-test rollback.
