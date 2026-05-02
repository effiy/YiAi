# core-unit-tests — Dynamic Checklist

> **Document Version**: v1.0 | **Last Updated**: 2026-05-03 | **Maintainer**: kimi-k2.6
> **Preconditions**: `02_requirement-tasks.md` and `03_design-document.md` exist and contain 3 main operation scenarios.

---

## General Check

- [ ] Document header is complete with version, date, maintainer
- [ ] Required chapters are present: General Check / Main Scenario Verification / Code Quality Check / Test Check / Check Summary
- [ ] Scenario count equals requirement-tasks scenario count (3 scenarios)
- [ ] Every scenario links to corresponding anchors in requirement-tasks and design-document

---

## Main Scenario Verification

### Scenario 1: Developer runs pytest and all core tests pass

| Precondition | Status |
|--------------|--------|
| `requirements.txt` installed | ⏳ Pending |
| `tests/` directory exists with `conftest.py` | ⏳ Pending |

| Operation Step | Verification Method | Status |
|----------------|---------------------|--------|
| Run `pytest tests/ -v` | Console output | ⏳ Pending |
| Verify test discovery | Console output | ⏳ Pending |
| Verify all tests pass | Exit code and summary | ⏳ Pending |

| Expected Result | Status |
|-----------------|--------|
| Exit code 0 | ⏳ Pending |
| Test count > 0 | ⏳ Pending |
| No import or fixture errors | ⏳ Pending |

- **Requirement-tasks anchor**: [Scenario 1](./02_requirement-tasks.md#scenario-1-developer-runs-pytest-and-all-core-tests-pass)
- **Design-document anchor**: [Scenario 1 Implementation](./03_design-document.md#scenario-1-developer-runs-pytest-and-all-core-tests-pass)

### Scenario 2: Execution engine tests cover core logic

| Precondition | Status |
|--------------|--------|
| `tests/test_execution.py` exists | ⏳ Pending |
| `executor.py` is importable | ⏳ Pending |

| Operation Step | Verification Method | Status |
|----------------|---------------------|--------|
| Run `pytest tests/test_execution.py -v` | Console output | ⏳ Pending |
| Verify `parse_parameters` tests | Console output | ⏳ Pending |
| Verify `execute_module` tests | Console output | ⏳ Pending |

| Expected Result | Status |
|-----------------|--------|
| All execution tests pass | ⏳ Pending |
| Whitelist enforcement verified | ⏳ Pending |
| Async/sync/generator paths exercised | ⏳ Pending |

- **Requirement-tasks anchor**: [Scenario 2](./02_requirement-tasks.md#scenario-2-execution-engine-tests-cover-core-logic)
- **Design-document anchor**: [Scenario 2 Implementation](./03_design-document.md#scenario-2-execution-engine-tests-cover-core-logic)

### Scenario 3: Upload module tests cover path safety and endpoints

| Precondition | Status |
|--------------|--------|
| `tests/test_upload.py` exists | ⏳ Pending |
| FastAPI `TestClient` available | ⏳ Pending |

| Operation Step | Verification Method | Status |
|----------------|---------------------|--------|
| Run `pytest tests/test_upload.py -v` | Console output | ⏳ Pending |
| Verify helper tests | Console output | ⏳ Pending |
| Verify endpoint tests | Console output | ⏳ Pending |

| Expected Result | Status |
|-----------------|--------|
| All upload tests pass | ⏳ Pending |
| Path traversal blocked | ⏳ Pending |
| Missing file returns 400 | ⏳ Pending |

- **Requirement-tasks anchor**: [Scenario 3](./02_requirement-tasks.md#scenario-3-upload-module-tests-cover-path-safety-and-endpoints)
- **Design-document anchor**: [Scenario 3 Implementation](./03_design-document.md#scenario-3-upload-module-tests-cover-path-safety-and-endpoints)

---

## Code Quality Check

- [ ] Test files follow pytest naming conventions (`test_*.py`)
- [ ] Fixtures are minimal and shared via `conftest.py`
- [ ] No hardcoded secrets or credentials in tests
- [ ] Tests clean up temp files and resources

---

## Test Check

- [ ] `pytest tests/ -v` runs without import errors
- [ ] `parse_parameters` tests cover dict, JSON string, invalid JSON, non-dict
- [ ] `execute_module` tests cover whitelist, async, sync, generator, errors
- [ ] `_validate_path` tests cover traversal and leading slash
- [ ] `_resolve_static_path` tests cover escape from base_dir
- [ ] Upload endpoint tests cover valid and invalid inputs
- [ ] `run_script` tests cover success, failure, and timeout

---

## Check Summary

### P0 Items

| Scenario | Items | Passed | Pass Rate |
|----------|-------|--------|-----------|
| Scenario 1 | 3 | 0 | 0% |
| Scenario 2 | 3 | 0 | 0% |
| Scenario 3 | 3 | 0 | 0% |
| Code Quality | 4 | 0 | 0% |
| Test Check | 7 | 0 | 0% |

### P1 Items

| Item | Status |
|------|--------|
| Upload endpoints tested with TestClient | ⏳ Pending |
| `run_script` timeout tested | ⏳ Pending |
| Settings monkeypatched for isolation | ⏳ Pending |

### P2 Items

| Item | Status |
|------|--------|
| Coverage report generated | ⏳ Pending |
| CI configuration added | ⏳ Pending |

### Overall Conclusion

⏳ All verification items are pending. Execute test implementation and run pytest to validate.

## Postscript: Future Planning & Improvements

- Add mock tests for MongoDB and OSS when integration test infrastructure is ready.
