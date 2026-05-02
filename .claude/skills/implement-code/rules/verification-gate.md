# Verification Gate Spec

> Verifiable entry verification decision logic. Gate A/B admission and evidence standards are sourced from [`implement-code-testing.md`](./implement-code-testing.md); this file supplements gate principles, fix loops, and final closure.

---

## 1. Gate Principles

- P0 not all passed, delivery prohibited
- On failure, code must be fixed; degrading P0 or modifying expected results is prohibited
- Self-fix上限 2 rounds, 3rd round outputs block report
- Human-confirmation type does not count toward P0 pass/fail determination
- Gate not executed / skipped / missing evidence = gate failure
- Gate A incomplete prohibits writing project code (see [`implement-code-testing.md`](./implement-code-testing.md) §2)
- Gate B incomplete prohibits entering stage 7 (see [`implement-code-testing.md`](./implement-code-testing.md) §3)

---

## 2. Check Item Classification

| Priority | Verification Method | Pass Condition |
|----------|---------------------|----------------|
| P0 | Manual browser + code review | UI interactive, data-testid complete, entry initialization correct |
| P1 | Manual + Jest | Error state display, boundary values, component rendering |
| P2 | Human | Visual consistency, responsive layout |

---

## 3. Verification Execution

Start real entry → operate per checklist → screenshot record → check JS console no errors → write back results (✅/❌)

---

## 4. Fix Loop

Round 1: root cause analysis → fix → re-verify
Round 2: same as above
Round 3: block report, stop execution

---

## 5. Status Write-Back

After verification completes, write back to `05_dynamic-checklist.md`: P0 passed → ✅ + date; P0 failed → ❌ + reason.

---

## 6. Dynamic Checklist Final Closure (Stage 7)

Before writing summary in stage 7, perform final closure on `05` (must follow order):

1. Write back `05` final status column/remarks (including date or evidence path)
2. Re-check item by item whether P0 is ✅ or explainable N/A
3. Write conclusion into `06_process-summary.md`

**Hard gate**: if any of the following is false, dynamic checklist final completion gate is not passed, must switch to block version summary:
- `05` has been updated per Gate B result, no "unverified yet marked ✅"
- Review record is traceable (locatable in `06` or `05` remarks)
- `06` conclusion is consistent with `05` current content

---

## 7. Prohibitions

- Degrading P0 to P1 to "pass" the gate
- Modifying checklist expected results
- Continuing after more than 2 fix rounds
- Changing status to ✅ without actual verification
