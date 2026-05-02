---
paths:
  - "docs/99_agent-runs/*_from-weekly.md"
  - "docs/weekly/**/*.md"
---

# Full-Document Breakdown from Weekly (from-weekly) Command Specification

> Core principles, review gates, and notification requirements follow `../SKILL.md`; this file only carries from-weekly-specific behavior details.

## Invocation

```bash
/generate-document from-weekly docs/weekly/2026-04-27~2026-05-03/weekly-report.md
```

Optional intents (stated by the user in conversation; if not stated, use default strategy):
- **Filter type**: Only process rows in the weekly table whose type is planning / project / system
- **Merge**: Specify multiple rows to merge into a single feature directory; highly overlapping improvements may be auto-merged (reason must be stated in the mapping table)

## Workflow

### Step 0: Breakdown and Mapping (before Step 1)

1. Parse table: extract actionable items row by row
2. Organize into requirements: generate `{feature-name}` and a one-sentence user story for each
3. Produce mapping table (mandatory disk write): `docs/99_agent-runs/<YYYYMMDD-HHMMSS>_from-weekly.md`
4. Zero items: when unable to parse, handle per SKILL.md principle #9 H4

### Steps 1-5: For each `{feature-name}` in sequence

Execute the standard 5-step workflow for each mapped feature name (see `workflow.md`). In Step 1, `docs-retriever` must be invoked separately for each feature directory.

### Step 6: Document Sync and Notification (once per round)

After all feature directories are completed, execute Step 6 only once this round:
- **import-docs**: Sync the entire `docs/`
- **wework-bot**: Send a summary notification whose body contains the source weekly report path and the feature directory list
