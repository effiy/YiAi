---
name: implement-code
description: |
  Code implementation orchestrator. 4-phase workflow driven by docs/<feature-name>/
  document set: preflight → implementation → validation → summary.
  Enforces import-docs → wework-bot at termination.
  Supports: /implement-code <feature-name> and /implement-code list.
user_invocable: true
lifecycle: code-pipeline
pipeline:
  stages:
    - id: "1"
      name: preflight
      title: Preflight + Impact Analysis
      agents: [codes-retriever, code-impact-analyzer, doc-impact-analyzer, codes-builder]
      gates: [specs-loaded, impact-chain-closed, doc-impact-closed, architecture-validated]
    - id: "2"
      name: implementation
      title: Code Implementation
      agents: [code-reviewer]
      gates: [p0-clear]
    - id: "3"
      name: validation
      title: Validation + Review
      agents: [code-reviewer]
      gates: [smoke-passed, p0-clear]
    - id: "4"
      name: summary
      title: Summary + Curation
      agents: [doc-quality-tracker, docs-builder, code-impl-reporter]
      gates: [quality-tracked, knowledge-persisted, report-generated]
    - id: "5"
      name: delivery
      title: Document Sync + Notification
      skills: [import-docs, wework-bot]
agents:
  required:
    - codes-retriever
    - code-impact-analyzer
    - doc-impact-analyzer
    - codes-builder
    - code-reviewer
    - doc-quality-tracker
    - docs-builder
    - code-impl-reporter
  optional:
    - test-page-builder
    - code-e2e-tester
    - test-markdown-builder
contracts:
  output: shared/agent-output-contract.md
  impact: shared/impact-analysis-contract.md
  evidence: shared/evidence-and-uncertainty.md
---

# implement-code

## Positioning

`implement-code` is the code implementation orchestrator: preflight documents and complete impact analysis → implement code by architecture → review and validate code quality → generate implementation summary.

### When to use

- A `docs/<feature-name>/` document set exists + user explicitly requests code implementation + phased progress is needed.

### When NOT to use

- Missing P0 documents (02+03+05) / user is still clarifying requirements / only trivial code patches needed.

## Input Prerequisites

### P0 (blocking if missing)

- `02_requirement-tasks.md` — user stories, scenarios, preconditions.
- `03_design-document.md` — modules, interfaces, constraints.
- `05_dynamic-checklist.md` — verifiable checklist items.

### P1/P2 (non-blocking)

- `01_requirement-document.md` — background and goals.
- `04_usage-document.md` — UI copy supplement.

## Commands

### Implement feature

```
/implement-code <feature-name>
```

### List available features

```
/implement-code list
```

Lists available feature directories under `docs/` (excluding `99_agent-runs`). Empty result suggests running `generate-document` first.

## Delta Rules (Beyond `code-pipeline` Template)

### 1. Per-module review

After each module is coded:

1. Invoke `code-reviewer`.
2. Fix P0 issues immediately. Log P1/P2 without blocking.
3. Self-check: P0 syntax cleared + architecture constraints confirmed + `data-testid` coverage + impact chain regression.

### 2. Dual-sided impact analysis

Code changes require both:

- **Code impact analysis** (`code-impact-analyzer`): track type changes, test coverage, build config impacts.
- **Document impact analysis** (`doc-impact-analyzer`): track reverse dependencies, cross-references, and example code freshness.

Both analyses must be performed in Stage 1 (Preflight) and revisited in Stage 3 (Validation).

### 3. Test-first evidence (Gate A)

Before writing implementation code, produce a test plan and acceptance criteria based on `02_requirement-tasks.md` main scenarios. Validate the MVP flow in a real entry point and preserve evidence.

Details: `rules/implement-code-testing.md` §2.

### 4. Smoke test mandate (Gate B)

After all modules are implemented, the AI MUST automatically execute a full main-flow smoke test. Failure blocks entry to the final stage.

Details: `rules/implement-code-testing.md` §3.

### 5. Knowledge curation

In the final stage, extract reusable patterns and pitfall records from the implementation. Consume `code-impl-reporter` output and write findings to the execution memory.

## Stop Conditions

Generate a blocking `06_implementation-summary.md` when:

- P0 prerequisite documents are missing.
- Impact chain is not closed.
- Code review P0 issues cannot be fixed.
- All modules are blocked.

Blocking summary format: record block reason and artifacts → write summary → write block status → `import-docs` + `wework-bot` block notification.

## Supporting Files

```
.claude/skills/implement-code/
├── SKILL.md                    # Entry + manifest (this file)
├── README.md                   # Quick start
└── rules/
    ├── orchestration.md        # Stage contracts and orchestration details
    ├── code-implementation.md  # Project-specific constraints
    ├── artifact-contracts.md   # Deliverable and write-back contracts
    ├── verification-gate.md    # Validation rules
    ├── implement-code-testing.md # Gate A/B admission and evidence (source of truth)
    ├── e2e-testing.md          # E2E directory and testid details
    ├── process-summary.md      # Summary document structure
    └── test-page.md            # Prototype page specification
```
