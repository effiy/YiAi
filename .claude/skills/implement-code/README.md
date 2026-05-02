# implement-code Quick Index

## Reading Order

1. [`SKILL.md`](./SKILL.md) — Applicability conditions, 4-stage overview, gates and stop conditions
2. [`rules/orchestration.md`](./rules/orchestration.md) — Stage contracts, document grounding, §3.4 coverage pre-check, skill/agent dispatch
3. [`rules/implement-code-testing.md`](./rules/implement-code-testing.md) — Gate A/B definitions and evidence standards
4. Per-stage rule files:
   - Stage 1: `implement-code-testing` + `e2e-testing` + `test-page`
   - Stage 2/6: `verification-gate`
   - Stage 3/4: `code-implementation`
   - Stage 7/Block: `process-summary`
5. [`rules/artifact-contracts.md`](./rules/artifact-contracts.md) — Artifact paths and write-back conventions
6. [`../../shared/impact-analysis-contract.md`](../../shared/impact-analysis-contract.md) — Impact chain analysis scope and P0 gates

## Source-of-Truth Division

| File | Responsibility |
|------|----------------|
| `SKILL.md` | Main orchestrator |
| `rules/orchestration.md` | Stage contracts and orchestration details |
| `rules/artifact-contracts.md` | Artifact paths, naming, write-back |
| `rules/implement-code-testing.md` | Gate A/B admission and evidence (source of truth) |
| `rules/verification-gate.md` | Gate principles, fix loops, final closure |
| `rules/code-implementation.md` | Coding constraints and self-checks |
| `rules/process-summary.md` | Summary document structure |
| `rules/e2e-testing.md` | E2E directories and data-testid |
| `rules/test-page.md` | Prototype page specs |
