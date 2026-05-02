Invoke the `import-docs` skill to sync local documents to the remote document API.

Arguments: `$ARGUMENTS`

Execution requirements:
- Default to `--dir docs --exts md` when no arguments are given.
- Must run the script's real `import` path; do not stop at a command draft.
- When the user asks to "see the list first", run `list` first, then `import` based on the results.
- Return statistics: created N, overwritten N, failed N (or note that docs does not exist and skip).
- Do not output the `API_X_TOKEN` in plaintext.
