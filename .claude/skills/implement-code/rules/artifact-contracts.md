# Artifact and Write-Back Contract

> Unifies file paths, naming conventions, and status fields across stages.

---

## 1. Document Set Path

```text
docs/<feature-name>/
├── 01_requirement-document.md
├── 02_requirement-tasks.md
├── 03_design-document.md
├── 04_usage-document.md
├── 05_dynamic-checklist.md
├── 06_process-summary.md
└── 07_project-report.md
```

- `06`: must be generated on normal completion or block
- `05`: write back status column / remarks / check summary after verification
- `01/02/03/04/07`: write back `## Implementation Status` after summary

When unable to locate: fallback `docs/99_agent-runs/<YYYYMMDD-HHMMSS>_implement-code.md`

---

## 2. Test Artifact Paths

All test files must be under `tests/` directory; landing in `src/`, `docs/`, or project root is prohibited. Subdirectory structure see [`e2e-testing.md`](./e2e-testing.md) §3.

---

## 3. Status Write-Back

**05 status values**: ⏳ unverified | 🏃 prototype verified | ✅ smoke passed | ❌ failed | ⚠️ needs human confirmation

**01/02/03/04/07 implementation status**: add `## Implementation Status`, containing: status (✅/🟡/⛔), update time, stage, verification result, associated summary, next step.

---

## 4. Naming Conventions

- `<feature-name>`: consistent with `docs/<feature-name>/`
- `<scenario-name>`: from `02_requirement-tasks.md`
- Abbreviation mixing prohibited

---

## 5. Prohibitions

- Changing status without actual verification
- Generating or retaining test files outside `tests/`
- Adding `## Implementation Status` to the same file repeatedly
