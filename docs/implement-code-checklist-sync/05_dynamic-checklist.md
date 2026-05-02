# implement-code-checklist-sync — Dynamic Checklist

> **Document Version**: v1.0 | **Last Updated**: 2026-05-02 | **Maintainer**: kimi-k2.6
> **Preconditions**: `02_requirement-tasks.md` and `03_design-document.md` exist and contain 3 main operation scenarios.

---

## General Check

- [ ] Document header is complete with version, date, maintainer
- [ ] Required chapters are present: General Check / Main Scenario Verification / Code Quality Check / Test Check / Check Summary
- [ ] Scenario count equals requirement-tasks scenario count (3 scenarios)
- [ ] Every scenario links to corresponding anchors in requirement-tasks and design-document

---

## Main Scenario Verification

### Scenario 1: implement-code completion updates 05 to match Gate B results

| Precondition | Status |
|--------------|--------|
| Feature has 02, 03, 05, 06 documents | ⏳ Pending |
| Gate B smoke tests executed | ⏳ Pending |
| process-summary.md rule updated with S0-5a | ⏳ Pending |

| Operation Step | Verification Method | Status |
|----------------|---------------------|--------|
| Run implement-code to completion | Process execution | ⏳ Pending |
| Open 05_dynamic-checklist.md after stage 7 | File inspection | ⏳ Pending |
| Compare 05 P0 statuses with 06 Gate B results | Side-by-side diff | ⏳ Pending |
| Verify evidence strings present in 05 | File inspection | ⏳ Pending |

| Expected Result | Status |
|-----------------|--------|
| 05 P0 items match 06 Gate B results | ⏳ Pending |
| Evidence includes stage, date, and method | ⏳ Pending |
| Write-back recorded in 06 §5 | ⏳ Pending |

- **Requirement-tasks anchor**: [Scenario 1](./02_requirement-tasks.md#scenario-1-implement-code-completion-updates-05-to-match-gate-b-results)
- **Design-document anchor**: [Scenario 1 Implementation](./03_design-document.md#scenario-1-implement-code-completion-updates-05)

### Scenario 2: generate-document init completion updates 05

| Precondition | Status |
|--------------|--------|
| `init.md` rule updated with closure step | ⏳ Pending |
| Init command generates 01-07 | ⏳ Pending |

| Operation Step | Verification Method | Status |
|----------------|---------------------|--------|
| Run `generate-document init` | Skill invocation | ⏳ Pending |
| Open 05_dynamic-checklist.md after init closure | File inspection | ⏳ Pending |
| Verify statuses are not all template defaults | File inspection | ⏳ Pending |

| Expected Result | Status |
|-----------------|--------|
| 05 shows updated statuses reflecting doc checks | ⏳ Pending |
| Evidence present for updated items | ⏳ Pending |

- **Requirement-tasks anchor**: [Scenario 2](./02_requirement-tasks.md#scenario-2-generate-document-init-completion-updates-05)
- **Design-document anchor**: [Scenario 2 Implementation](./03_design-document.md#scenario-2-generate-document-init-completion-updates-05)

### Scenario 3: Inconsistency detected and blocked

| Precondition | Status |
|--------------|--------|
| orchestration.md rule updated with stage 7.5 | ⏳ Pending |
| 05 and 06 exist with deliberate mismatch | ⏳ Pending |

| Operation Step | Verification Method | Status |
|----------------|---------------------|--------|
| Introduce mismatch in 05 or 06 | Manual edit | ⏳ Pending |
| Run consistency check | Script or agent | ⏳ Pending |
| Observe block or warning | Console output | ⏳ Pending |
| Apply override and verify logging | Console and file inspection | ⏳ Pending |

| Expected Result | Status |
|-----------------|--------|
| Block prevents wework-bot notification | ⏳ Pending |
| Mismatch report shows exact items | ⏳ Pending |
| Override reason logged in 06 | ⏳ Pending |

- **Requirement-tasks anchor**: [Scenario 3](./02_requirement-tasks.md#scenario-3-inconsistency-detected-and-blocked)
- **Design-document anchor**: [Scenario 3 Implementation](./03_design-document.md#scenario-3-inconsistency-detected-and-blocked)

---

## Code Quality Check

- [ ] All rule file edits preserve existing structure and formatting
- [ ] No circular dependencies introduced between rules
- [ ] Process summary and init rules remain independently readable
- [ ] New rule sections reference upstream documents correctly

---

## Test Check

- [ ] Mock implement-code delivery: verify 05 updated after process summary
- [ ] Mock init delivery: verify 05 updated after init closure
- [ ] Deliberate mismatch: verify block triggers before wework-bot
- [ ] Override path: verify notification proceeds with logged reason
- [ ] Idempotency: re-running process summary does not corrupt 05 evidence

---

## Check Summary

### P0 Items

| Scenario | Items | Passed | Pass Rate |
|----------|-------|--------|-----------|
| Scenario 1 | 4 | 0 | 0% |
| Scenario 2 | 3 | 0 | 0% |
| Scenario 3 | 4 | 0 | 0% |
| Code Quality | 4 | 0 | 0% |
| Test Check | 5 | 0 | 0% |

### P1 Items

| Item | Status |
|------|--------|
| Consistency check script implemented | ⏳ Pending |
| Inconsistency blocks notification | ⏳ Pending |
| Write-back is idempotent | ⏳ Pending |

### P2 Items

| Item | Status |
|------|--------|
| Auto-generated 05 diff section | ⏳ Pending |

### Overall Conclusion

⏳ All verification items are pending. Execute rule updates and mock deliveries to validate.

## Postscript: Future Planning & Improvements

- Automate consistency check with a standalone script.
