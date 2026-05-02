# implement-code Testing Gates (Source of Truth)

> Gate A/B admission, evidence, and block conditions. UI details see [`e2e-testing.md`](./e2e-testing.md), [`test-page.md`](./test-page.md).

---

## 1. Two Mandatory Gates

| Gate | Stage | Meaning |
|------|-------|---------|
| **Gate A** | Stage 1 | Real entry main-path MVP verification + traceable evidence; passing required before writing code |
| **Gate B** | Stage 6 | AI automatically executes P0 main-flow smoke; failure blocks entry to stage 7 |

---

## 2. Gate A: Pre-Code MVP

- Must align with `02` main user story / P0 scenario + `05` P0 acceptance statement
- Entry is real: use project-convention startup method; verbal deduction or pseudo-pages prohibited
- MVP covers only one main path (shortest closed loop): core behavior triggerable, core result observable
- Evidence types (all required): command + exit code / log excerpt / screenshot stored in `tests/screenshots/` / checklist tick
- "Tried before" / "should work" prohibited as pass basis

### Relationship with TDD/Automation

- When automation infrastructure exists: write failing case / minimum reproduction script first, then enter implementation
- When zero build / no runner: solidify minimum reproduction steps into `tests/` checklist or one-click script

### Guidance by Form

| Form | Gate A Approach |
|------|-----------------|
| Frontend page | Local service up → main flow walked through → checklist + screenshot |
| Browser extension | Extension loaded → visible path walked through → evidence path stated |
| Node/CLI | Conventional command runs with main parameters → log landed in `tests/` |

---

## 3. Gate B: Post-Code Smoke

- Must cover all `05` P0 main-path items; non-main-path P0 must be labeled N/A + reason, silently skipping prohibited
- Actually executed by AI (Playwright preferred; if not installed, equivalent scriptable path)
- Main path end-to-end runs through once; ≤2 fix rounds allowed (see [`verification-gate.md`](./verification-gate.md) §4)
- Produces reviewable artifacts: terminal output, HTML report, `tests/traces/`, etc.
- Failure blocks entry to stage 7, triggers gate-anomaly notification

---

## 4. Division with e2e-testing

| Role | Responsibility |
|------|----------------|
| [`../../e2e-testing/SKILL.md`](../../e2e-testing/SKILL.md) | Scenario strategy, case skeleton, selectors and mock suggestions |
| **This file** | Pins the above outputs to Gate A/B admission and evidence standards |

---

## 5. Prohibitions

- Modifying project source code before Gate A completes (test skeleton and prototype pages excluded)
- Substituting code review for Gate B execution or fabricating results
- Placing test artifacts outside `tests/` while claiming gate satisfaction
