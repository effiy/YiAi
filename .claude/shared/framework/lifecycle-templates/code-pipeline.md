---
paths:
  - "shared/framework/lifecycle-templates/code-pipeline.md"
---

# Lifecycle Template: Code Pipeline

**Inherits**: `default-pipeline`

This template extends the default pipeline with rules specific to code implementation skills (e.g., `implement-code`). Skills that use this template declare `lifecycle: code-pipeline` in their frontmatter.

---

## Delta Rules (Beyond Default Pipeline)

### 1. Git Branch Enforcement

The entire pipeline MUST run on branch `feat/<feature-name>`, matching the `docs/<feature-name>/` directory. Any code change must be preceded by branch creation or checkout. Working on `main`/`master` is prohibited.

### 2. Gate A: Test-First

Before writing implementation code, produce a test plan and acceptance criteria based on `02_requirement-tasks.md` main scenarios. Validate the MVP flow in a real entry point and preserve evidence.

Details: See `rules/implement-code-testing.md` §2.

### 3. Gate B: Smoke Test

After all modules are implemented, the AI MUST automatically execute a full main-flow smoke test. Failure blocks entry to the final stage.

Details: See `rules/implement-code-testing.md` §3.

### 4. Per-Module Review

After each module is coded:

1. Invoke `code-reviewer`.
2. Fix P0 issues immediately. Log P1/P2 without blocking.
3. Self-check: P0 syntax cleared + architecture constraints confirmed + `data-testid` coverage + impact chain regression.

### 5. Full Review at Stage 3

Before declaring implementation complete:

1. Invoke `code-reviewer` for a full-project review.
2. Execute Gate B (smoke test).
3. Verify all P0 checklist items from `05_dynamic-checklist.md`.

Exit criteria: Zero unresolved P0 issues + all P0 checklist items pass.

### 6. Impact Analysis (Dual-Sided)

Code changes require both:

- **Code impact analysis** (`code-impact-analyzer`): Track type changes, test coverage, build config impacts.
- **Document impact analysis** (`doc-impact-analyzer`): Track reverse dependencies, cross-references, and example code freshness.

Both analyses must be performed in Stage 1 (Pre-flight) and revisited in Stage 3 (Validation).

### 7. Knowledge Curation

In the final stage, extract reusable patterns and pitfall records from the implementation. Consume `code-impl-reporter` output and write findings to the execution memory.

### 8. Document Postscript (Self-Improvement)

The `06_process-summary.md` produced by this pipeline must append two standardized reflection sections at the end:

1. **Workflow Standardization Review** — four-question retrospective on the implementation process. See `skills/self-improving/rules/collection-contract.md` §3.
2. **System Architecture Evolution Thinking** — architecture reflection for the implemented feature. See `skills/self-improving/rules/collection-contract.md` §4.

These sections are consumed by the `self-improving` skill for weekly aggregation.
