# core-unit-tests

> **Document Version**: v1.0 | **Last Updated**: 2026-05-02 | **Maintainer**: kimi-k2.6 | **Tool**: Claude Code
>
> **Related Documents**: [Requirement Tasks](./02_requirement-tasks.md) | [Design Document](./03_design-document.md) | [Usage Document](./04_usage-document.md) | [CLAUDE.md](../../CLAUDE.md)

[Feature Overview](#feature-overview) | [User Stories](#user-stories) | [Acceptance Criteria](#acceptance-criteria) | [Feature Details](#feature-details)

---

## Feature Overview

YiAi currently has no automated test suite. The `tests/` directory does not exist, `requirements.txt` lacks testing dependencies, and core business logic in `src/services/execution/executor.py` and `src/api/routes/upload.py` is verified only through manual inspection. This feature bootstraps a `tests/` directory, adds pytest and related dependencies, and implements core unit tests for the execution engine and upload module to establish a safety net for future changes.

**Scope**: Create `tests/` with `conftest.py`, unit tests for `executor.py` functions, and unit tests for `upload.py` helpers and endpoints.

**Non-goals**: Full integration tests for MongoDB or OSS; E2E tests for the entire API; coverage for non-core modules.

- 🎯 **Goal**: Establish a runnable pytest suite covering execution and upload core logic
- ⚡ **Impact**: Prevents regressions in dynamic module execution and file handling
- 📖 **Clarity**: Tests serve as executable documentation for edge cases and error handling

---

## User Stories and Feature Requirements

**Priority**: 🔴 P0 | 🟡 P1 | 🟢 P2

**One user story corresponds to one `docs/<feature-name>/` numbered set (01–05, 07).**

| User Story | Acceptance Criteria | Process-Generated Documents | Output Smart Documents |
|------------|---------------------|----------------------------|------------------------|
| 🔴 As a developer, I want a `tests/` directory with core unit tests for the execution engine and upload module, so that code quality and maintainability are improved and regressions are caught early.<br/><br/>**Main Operation Scenarios**:<br/>- Developer runs `pytest` and all core tests pass<br/>- Execution engine whitelist, parameter parsing, and async invocation are tested<br/>- Upload module path validation, file operations, and endpoints are tested | 1. `tests/` directory exists with `conftest.py` (P0)<br/>2. `pytest` and `pytest-asyncio` added to `requirements.txt` (P0)<br/>3. `parse_parameters` tested with dict, JSON string, invalid JSON, and non-dict (P0)<br/>4. `execute_module` tested with whitelist enforcement, async/sync/generator execution, and error handling (P0)<br/>5. `_validate_path`, `_resolve_static_path`, `_safe_rename` tested for traversal prevention and type checks (P0)<br/>6. Upload endpoints tested with FastAPI `TestClient` for valid and invalid inputs (P1) | [Requirement Tasks](./02_requirement-tasks.md)<br/>[Design Document](./03_design-document.md)<br/>[Project Report](./07_project-report.md) | [Generate Document Skill](../../.claude/skills/generate-document/SKILL.md)<br/>[Requirement Document Specification](../../.claude/skills/generate-document/rules/requirement-document.md)<br/>[Requirement Document Template](../../.claude/skills/generate-document/templates/requirement-document.md)<br/>[Requirement Document Checklist](../../.claude/skills/generate-document/checklists/requirement-document.md) |

---

## Document Specifications

- One numbered set corresponds to one user story
- Anti-hallucination: content that cannot be determined from repository facts/upstream write `> Pending confirmation (reason: …)`

---

## Acceptance Criteria

### P0 — Core (cannot release without)

1. `tests/` directory created with `conftest.py`
2. `pytest>=8.0` and `pytest-asyncio>=0.23` added to `requirements.txt`
3. `parse_parameters` unit tests cover all branches
4. `execute_module` unit tests cover whitelist, async/sync/generator, and errors
5. Upload helper unit tests cover path validation, resolution, and safe rename
6. `pytest tests/ -v` runs successfully and all new tests pass

### P1 — Important (recommended)

7. Upload endpoints tested with `TestClient` (FastAPI)
8. `run_script` tested with success, failure, and timeout paths
9. Test settings monkeypatch or override for isolated execution

### P2 — Nice-to-have

10. Coverage report generated with `pytest --cov`
11. CI configuration (GitHub Actions) to run tests on push

---

## Feature Details

### tests/ Directory Bootstrap

- **Description**: Create `tests/` at project root with `conftest.py` for shared fixtures.
- **Boundaries**: Only core modules; integration with MongoDB/OSS mocked or skipped.
- **Value**: Provides a home for all future tests.

### Execution Engine Unit Tests

- **Description**: Test `executor.py` functions: `parse_parameters`, `run_script`, `execute_module`.
- **Boundaries**: Does not test SSE streaming in `execution.py` route layer (P2).
- **Value**: Catches regressions in dynamic module execution, the project's core extensibility mechanism.

### Upload Module Unit Tests

- **Description**: Test `upload.py` helpers and endpoints: path validation, file CRUD, OSS fallback.
- **Boundaries**: Does not test actual OSS upload (requires credentials); mocks OSS client.
- **Value**: Prevents path traversal and file operation regressions.

---

## Usage Scenario Examples

### Scenario 1: Developer runs pytest after changes

- **Background**: Developer modifies `executor.py` whitelist logic.
- **Operation**: Runs `pytest tests/ -v`.
- **Result**: All execution engine tests pass; developer confident no regression.
- 📋 **Verification**: Console shows green test output.

### Scenario 2: Path traversal attempt is caught

- **Background**: Malicious input attempts `../etc/passwd`.
- **Operation**: Upload endpoint receives malicious path.
- **Result**: `_validate_path` raises `BusinessException`; test asserts correct error code.
- 📋 **Verification**: Test case `test_validate_path_traversal` passes.

### Scenario 3: New feature adds test coverage

- **Background**: Team adds a new endpoint.
- **Operation**: Developer writes test in `tests/` following existing patterns.
- **Result**: PR includes test; review verifies coverage.
- 📋 **Verification**: `pytest` includes new test and passes.

## Postscript: Future Planning & Improvements

- Expand tests to cover RSS scheduler, chat service, and maintenance endpoints.
- Add property-based tests for path validation using Hypothesis.
