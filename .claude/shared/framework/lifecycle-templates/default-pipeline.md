---
paths:
  - "shared/framework/lifecycle-templates/default-pipeline.md"
---

# Lifecycle Template: Default Pipeline

This is the base lifecycle template inherited by all multi-stage skills unless they specify otherwise. It defines universal mechanics: pre-flight, per-stage logging, severity gating, stop conditions, and mandatory post-flight steps.

Skills that inherit this template (`lifecycle: default-pipeline`) only document their *delta* rules in body text. They do not repeat these universal rules.

---

## Pre-Flight (Before Stage 0)

1. **Git branch check** (git repositories only): Ensure the current branch is `feat/<feature-name>`. If not, create or check it out. Never work on `main`/`master`.
2. **Document precheck**: Verify that P0 prerequisite documents exist. Missing P0 documents is a blocking condition.
3. **Environment probe**: Check for required environment variables (`API_X_TOKEN`). Missing tokens may trigger a downgrade (skip sync, but still notify).
4. **Execution memory load**: If the skill uses adaptive planning, read `docs/.memory/execution-memory.jsonl` before Stage 0.

---

## Per-Stage Mechanics

### Logging (Mandatory)

After every skill/agent/MCP/shared interaction, append an orchestration log:

```bash
node .claude/skills/generate-document/scripts/log-orchestration.js \
  --skill <skill-name> \
  --kind <skill|agent|mcp|shared|other> \
  [--name <identifier>] \
  [--scenario "<operation context>"] \
  [--case <good|bad|neutral>] \
  [--tags "<tag1,tag2>"] \
  [--lesson "<improvement note>"] \
  [--text "<one-line summary>"]
```

### Severity Gating

- **P0 (Blocking)**: Must be resolved before saving or advancing. Examples: syntax errors, missing required sections, hallucinated facts.
- **P1 (Warning)**: Should be fixed, but may be deferred if time-constrained. Log and track.
- **P2 (Suggestion)**: Nice-to-have improvements. Track for trend analysis only.

A stage is **blocked** if any P0 gate is not satisfied. The skill must:
1. Attempt one self-repair round.
2. If still blocked, mark the stage as failed and proceed to Stop Conditions.

### Agent Output Validation

Before adopting an agent's output, validate its JSON contract appendix:

```bash
node .claude/skills/implement-code/scripts/validate-agent-output.js \
  --agent <agent-name> \
  --text "<raw output>"
```

If validation fails, retry once with correction instructions. If it fails again, treat as an agent invocation failure and follow Stop Conditions.

---

## Post-Flight (After Final Stage)

Every skill MUST execute these two steps in order before declaring completion:

1. **`import-docs`**: Synchronize generated or updated documents to the external doc index.
2. **`wework-bot`**: Send a completion, block, or gate-failure notification.

Neither step may be skipped, reordered, or silently downgraded.

### Notification Content

The wework-bot message must include:
- **Type**: Completion, Block, or Gate Failure.
- **Conclusion**: One-line outcome.
- **Artifacts**: List of files created or updated.
- **Metrics**: Elapsed time, session usage, model name, and tool count.
- **Next Actions**: Up to 2 actionable recommendations.

---

## Stop Conditions

The skill must halt and generate a blocking summary (`06_process-summary.md` or equivalent) when any of the following occur:

- P0 prerequisite documents are missing.
- Impact chain cannot be closed and no downgrade path exists.
- P0 review issues cannot be resolved after one self-repair round.
- All modules are blocked.
- An agent invocation fails twice in a row.

When stopping:
1. Record the block reason and partial artifacts.
2. Generate the blocking summary.
3. Write block status back to all affected documents.
4. Execute `import-docs` + `wework-bot` with a block notification.

---

## Incremental Update Support

All pipelines support three change levels. Skills with document-pipeline or code-pipeline templates extend these defaults:

| Level | Name | Stage Strategy |
|-------|------|----------------|
| T1 | Micro | Re-run target stage only. Reuse previous impact analysis and architecture. |
| T2 | Local | Re-run target stage + directly affected downstream stages. Partial impact analysis. |
| T3 | Scope | Full pipeline re-run. Complete impact analysis and architecture review. |

The change level is determined during Stage 0 (adaptive planning) and must not be downgraded to save time.
