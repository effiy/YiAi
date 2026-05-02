---
paths:
  - "docs/weekly/**/*.md"
---

# Weekly (weekly) Command Specification

> Core principles, review gates, and notification requirements follow `../SKILL.md`; this file only carries weekly-specific behavior details.

## Invocation

```bash
/generate-document weekly                           # This week's weekly report
/generate-document weekly 2026-04-29                # Assign to its natural week by given date
/generate-document weekly 2026-04-27~2026-05-03     # By natural week start/end
```

## Output

- Path: `docs/weekly/<YYYY-MM-DD>~<YYYY-MM-DD>/weekly-report.md`
- Update mechanism: Overwrite within same week, patch version `+1`

## Workflow

**Execute to completion in one go (mandatory)**: Weekly report generation must complete in a single round, must not interrupt for any non-blocking reason. Missing information write "pending confirmation" and continue; only when H1-H4 blocking threshold is hit may interruption be allowed. See [orchestration.md §4](../orchestration.md#4-blocking-points).

1. Determine coverage period: calculate to natural week (Monday to Sunday) based on parameter
2. Dynamic context read: Execute `collect-weekly-kpi.js --with-logs`, read project basic files, orchestration logs, existing document set
3. Generate weekly report: Strictly follow `rules/weekly-report.md` structure output
4. Mermaid review: Invoke `doc-mermaid-expert` to review and write back
5. Self-check: Load `checklists/weekly-report.md`, P0 all passed before saving as passed status
6. Save: Write to `docs/weekly/<natural-week>/weekly-report.md`
7. Step 6: `import-docs` first, then `wework-bot`

## Coverage Period Calculation Rules (Natural Week)

- Monday is start day, Sunday is end day
- File name and title uniformly use start/end dates: `YYYY-MM-DD~YYYY-MM-DD`
- Given date automatically expands to that natural week start/end
- Start~end must validate start is Monday, end is Sunday; if not satisfied, recalculate by natural week
