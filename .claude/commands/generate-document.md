Invoke the `generate-document` skill to generate or update documentation.

Arguments: `$ARGUMENTS`

## Command cheat sheet

| Command | Purpose |
|---------|---------|
| `init` | Initialize project base files + full `docs/project-init/` document set |
| `<feature-name>-<description>` | Generate/update document set under `docs/<feature-name>/` (01–05, 07) |
| `weekly [date]` | Generate/update this week's weekly report |
| `from-weekly <weekly-path>` | Decompose "future planning" from a weekly report into multiple feature document sets |

All commands are idempotent; existing documents are incrementally updated. Every run must end with `import-docs` then `wework-bot`.

See `skills/generate-document/SKILL.md` and `README.md` for full rules.
