# E2E Testing Spec

> Directory structure, data-testid, mock and automation preferences. Gate A/B admission and evidence standards are sourced from [`implement-code-testing.md`](./implement-code-testing.md).

---

## 1. Core Constraints

| # | Constraint |
|---|------------|
| E0-1 | Every scenario has explicit verification steps and expected results (from `05`) |
| E0-2 | Interactive UI elements must be marked with `data-testid`, format `<feature-name>-<element-name>` |
| E0-3 | Assertions must come from `05` expected results |
| E0-4 | API mock is isolated through hooks/store layer |
| E0-5 | Test file path: `tests/e2e/<feature-name>/` |
| E0-6 | Mock is limited to `tests/` directory; production code prohibits mock |

---

## 2. Verification Methods

| Method | Purpose |
|--------|---------|
| Real entry MVP (mandatory, Gate A) | Main flow minimum viable path + evidence |
| Manual browser | Operate per checklist + screenshot |
| Code review | data-testid, entry initialization, component registration |
| Build verification | JS console no errors, components render normally |
| AI auto smoke (mandatory, Gate B) | End-to-end main flow + pass/fail evidence |

Playwright is preferred for Gate B; when not installed, equivalent automation must be completed via scriptable command + reviewable log, manual substitution is not allowed.

---

## 3. File Structure

```text
tests/e2e/<feature-name>/
├── <scenario-name>-checklist.md    # Verification checklist + screenshots
└── fixtures/                 # Mock data (optional)
```

---

## 4. Prohibitions

- Importing project source code in E2E tests
- Only testing success paths without covering failure branches
- Using meaningless placeholders for mock data
- Generating test files outside `tests/`
- Assuming Playwright is available
