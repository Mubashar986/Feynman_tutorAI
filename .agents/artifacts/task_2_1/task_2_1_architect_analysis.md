# Narrsistic Pluto Analysis & Root Cause Analysis (RCA)
## Task 2.1: Exam Template Data Models & Syllabus Parser — Defect Analysis for ISSUE-0004

* **Classification:** Bug Fix / Dependency Import Defect
* **Risk Profile:** Low
* **Confidence:** High — directly inspected codebase and terminal traceback

---

### 0. Task Intake
* **Acceptance Criteria Status:** Falsifiable reproduction: `py -3.14 -m pytest backend/tests/` failed during module discovery due to top-level `import yaml`.
* **Assumptions Ledger:** Standard Python 3.14 environment has built-in `json` module; `pyyaml` is an optional external package.

---

### 1. Architectural Compliance & Codebase Topology
* **Prescriptive Model Alignment:** Zero silent dependency ingestion policy (Rule 20). Platform primitives and standard library modules (`json`) must always be preferred over third-party dependencies unless strictly approved.
* **Blast Radius:** Internal parsing function in `backend/app/curriculum/service.py`.
* **Semver Classification:** PATCH (internal bugfix).

---

### 2. Defect Diagnostics & Root Cause Analysis (5-Whys)
1. **Why did the test suite fail?** Pytest failed during test collection with `ModuleNotFoundError: No module named 'yaml'`.
2. **Why was `yaml` imported?** `service.py` attempted to support YAML parsing by importing `yaml` at top-level.
3. **Why was `pyyaml` not found?** `pyyaml` is not part of Python's standard library and is not installed in the target environment.
4. **Why was this not caught at edit time?** The import was written under the assumption that `pyyaml` was present in the virtual environment.
5. **Root Cause:** Hard top-level import of an optional non-standard library package without defensive conditional fallback (`try/except ImportError`).

---

### 3. Alternative Engineering Solutions (3 Approaches)

#### Approach 1: Defensive Conditional Import with Native JSON Priority (Recommended)
* **Implementation:**
  ```python
  import json
  try:
      import yaml
      HAS_YAML = True
  except ImportError:
      yaml = None
      HAS_YAML = False
  ```
  In `parse_yaml_or_json()`, parse JSON first using standard library `json.loads()`. If JSON fails and `HAS_YAML` is true, use `yaml.safe_load()`. If `HAS_YAML` is false, return clear 422 error advising that JSON is standard and YAML requires `pyyaml`.
* **Pros:** Zero new dependencies, 100% resilient across all Python environments.
* **Cons:** YAML format requires `pyyaml` to be installed if user explicitly provides YAML.

#### Approach 2: Hard-require and install `pyyaml` via pip
* **Implementation:** Run `pip install pyyaml`.
* **Cons:** Violates zero silent library ingestion policy when native JSON handles 100% of API payloads.

#### Approach 3: Pure JSON-only parsing
* **Implementation:** Remove all YAML references and only support JSON blueprints.
* **Cons:** Drops potential YAML convenience if a developer installs `pyyaml` later.

---

### 4. Comparative Matrix

| Approach | Complexity | Perf / Security | Test Effort | Rollout Risk | Recommendation Weight |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Approach 1 (Conditional Import + JSON Priority)** | Low (5 lines) | High (Native JSON) | Minimal | Low | **RECOMMENDED (0.95)** |
| **Approach 2 (Pip Install PyYAML)** | Medium | Medium (C-extension risk) | Low | Medium | 0.40 |
| **Approach 3 (JSON-only)** | Low | High | Minimal | Low | 0.80 |

---

### 5. Principal Synthesis & Recommendation

**Recommendation:** Execute **Approach 1**. Wrap `yaml` in a conditional import and use Python's built-in `json` module as the primary parser. Update `backend/tests/test_exam_templates.py` to test JSON directly and conditionally test YAML only if available.
