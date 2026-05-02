---
name: e2e-testing
description: |
  Design E2E test schemes for UI user flow scenarios, recommending manual browser
  verification + data-testid strategy. Used when dynamic checklists or requirement
  tasks contain UI operation scenarios. When combined with implement-code, output
  must satisfy Gate A/B (see ../implement-code/rules/implement-code-testing.md).
user_invocable: true
lifecycle: default-pipeline
---

# e2e-testing

## Purpose

Transform main operation scenarios from requirement tasks into executable E2E test schemes, outputting test strategy, case skeletons, and verification points.

**Test-first principle**: this skill emphasizes "test scheme before code implementation." Before `implement-code` enters Stage 2 (code implementation), a viable test strategy and acceptance criteria must be produced first; every line of code implementation must correspond to a defined test verification point.

This skill defines test scheme methods and output format. For parallel expert roles or required questions, use `../../agents/code-e2e-tester.md`. Boundaries: `../../shared/agent-skill-boundaries.md`.

### Additional Constraints When Combined with implement-code

- **Before coding (Gate A) — test first**: deliverables must support "main path MVP on real entry"—for example, actionable `tests/e2e/<feature>/…-checklist.md` steps, recommended `data-testid` list, and consistency with P0 scenarios in `02`/`05`. **Before code implementation begins, test scheme and acceptance criteria must be ready.**
- **After coding (Gate B)**: case skeletons must be automatable by AI (prefer Playwright); if scenarios lack sufficient assertions, explicitly write "insufficient precondition information: …" rather than fabricating pass conditions.
- **Source of truth**: admission baseline (what counts as evidence, what blocks) is defined by **`../implement-code/rules/implement-code-testing.md`**; this skill does not redefine Gate A/B.

## Input

- **Scenario list**: operation scenarios from requirement tasks (name + preconditions + operation steps + expected results)
- **Tech stack**: such as Vue3 + Vite (for inferring selector strategy)
- **Key code paths**: involved modules from design documents (optional)

## Workflow

1. Analyze each scenario and determine test type (UI interaction / data flow / permission / boundary)
2. Design verification step checklist for each scenario
3. Give selector strategy (prioritize `data-testid`, second choice semantic tags)
4. Identify external dependencies that need mocking
5. Give test data strategy

## Output Format (per scenario)

```
Scenario: <scenario name>
Test type: UI interaction / data flow / permission / boundary
Verification checklist:
  test('<scenario name>', async ({ page }) => {
    // preconditions
    // operation steps
    // assertions
  });
Selector strategy: <description>
Mock dependencies: <interfaces/modules to mock, or "none">
Test data: <suggested test data construction method>
```

## Conventions (when applicable)

- Selector priority: `data-testid` > semantic tags (`button[type=submit]`) > text content
- Test file location: `tests/e2e/<feature>.spec.js`
- Base entry: if no automation runner, start service locally or open entry page directly (per project status)

## Usage Rules

- Test cases can only be generated based on **provided scenarios**; do not add scenarios not present in requirement tasks.
- If scenario descriptions are insufficient to infer assertion conditions, output "insufficient precondition information, needs supplement: <missing content>."
