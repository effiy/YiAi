Invoke the `code-review` skill to audit code for standards compliance.

Arguments: `$ARGUMENTS`

Execution requirements:
- Must base the review on actually read code; do not infer contents of unseen files.
- Review dimensions: project-specific (entry initialization, state management, component registration/export, code structure) + general quality (readability, boundaries, security, performance).
- Output graded by P0/P1/P2 with file paths and fix recommendations.
- When a file cannot be read, state the path and skip it.
