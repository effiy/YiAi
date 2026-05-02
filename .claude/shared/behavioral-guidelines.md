# Behavioral Guidelines

> Reduce common LLM coding mistakes. Merge with project-specific instructions as needed.
>
> **Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Completion and Interruption Require Notification

**When a flow completes or is interrupted, you must use wework-bot to send a notification and import-docs to sync documents.**

- Flow completion (success / includes P0 failure): first execute `import-docs` to sync `docs`, then call `wework-bot` to send completion notification. The `☁️ Document sync` line must reference real `import-docs` statistics; do not fabricate numbers.
- Flow interruption / block / gate anomaly: likewise execute `import-docs` first (record real numbers even on failure), then call `wework-bot` to send block/gate-anomaly notification. Notification must include blocked stage, reason, evidence, and recovery point.
- Notification order: **first `import-docs`, then `wework-bot`** — do not send notification before sync completes, otherwise `☁️ Document sync` cannot be filled with real values.
- Notification send failure: record failure reason (API status code, desensitized route, model, tool, last update time) into `06_process-summary.md` or `docs/99_agent-runs/` fallback log. Do not silently omit.
- Missing `API_X_TOKEN`: `import-docs` skips sync and records reason; `wework-bot` notification must still be sent, omitting the `☁️ Document sync` line with a one-line note: "`API_X_TOKEN` not detected; manual sync available later."

---

**These guidelines are working when:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, clarifying questions come before implementation rather than after mistakes, and every flow interruption/completion produces a verifiable group notification.
