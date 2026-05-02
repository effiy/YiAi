Invoke the `implement-code` skill to implement code.

Arguments: `$ARGUMENTS`

Execution requirements:
- Must implement based on `docs/<feature-name>/02_requirement-tasks.md` and `03_design-document.md`; do not code in a vacuum without upstream documents.
- After completion, must write `06_process-summary.md`, then execute `import-docs` → `wework-bot` to close out.
- When upstream documents are missing, state the missing path and abort.
