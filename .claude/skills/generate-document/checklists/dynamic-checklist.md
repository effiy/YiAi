# Dynamic Checklist · Self-Check List

> **Related specs**: [Dynamic Checklist Spec](../rules/dynamic-checklist.md) | [General Document Checklist](./general-document.md)

## P0 — Must Pass

- Preconditions are met (02 requirement-tasks and 03 design-document exist and contain main operation scenarios / implementation chapters)
- Document header is complete
- Required chapters are present: General Check / Main Scenario Verification / Code Quality Check / Test Check / Check Summary
- Scenario count equals requirement-tasks scenario count; each scenario contains precondition / operation step / expected result three tables
- Every scenario links to the corresponding anchor in requirement-tasks and design-document
- Code paths are real and exist
- No fabricated skills (verification tools only contain find-skills return values or "manual review")
- General check four fixed lines present
- Template was not used

## P1 — Should Pass

- Verification methods are concrete (not generalized statements)
- Priority determinations are reasonable
- Code quality and test check fixed lines are complete
- Links are resolvable

## P2 — Nice to Have

- Check summary three sub-sections are complete
- Icons are used consistently
