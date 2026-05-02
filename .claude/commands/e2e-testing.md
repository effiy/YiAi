Invoke the `e2e-testing` skill to design an E2E test plan.

Arguments: `$ARGUMENTS`

Execution requirements:
- Test cases must be generated solely from provided scenarios; do not add scenarios not present in the requirement tasks.
- When used with `implement-code`, output must satisfy the Gate A/B minimum thresholds (see `../implement-code/rules/implement-code-testing.md`).
- When scenario information is insufficient to infer assertion conditions, output "insufficient prerequisite information, need to supplement: <missing>".
- Selector priority: `data-testid` > semantic tag > text content.
