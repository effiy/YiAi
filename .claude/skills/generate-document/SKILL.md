---
name: generate-document
description: |
  Documentation generation orchestrator. Creates or updates the full numbered document set (01–05, 07)
  under docs/<feature-name>/. Drives a 5-step workflow with three-layer review gates.
  Enforces import-docs → wework-bot at termination; interruptions and completions alike.
  Supports: /generate-document <feature-name>-<description>, init, weekly, from-weekly <path>.
user_invocable: true
lifecycle: document-pipeline
pipeline:
  stages:
    - id: "0"
      name: adaptive-planning
      title: Adaptive Planning
      agents: [doc-planner]
      gates: [execution-memory-ready]
      optional: true
    - id: "1"
      name: discovery
      title: Discovery & Specification Retrieval
      agents: [docs-retriever]
      gates: [specs-loaded]
    - id: "2"
      name: impact-analysis
      title: Upstream Grounding & Impact Analysis
      agents: [doc-impact-analyzer]
      gates: [impact-chain-closed]
    - id: "3"
      name: architecture
      title: Expert Architecture Design
      agents: [codes-builder, doc-architect]
      gates: [architecture-validated]
      parallel: true
    - id: "4"
      name: generation
      title: Per-Document Generation & Self-Review
      agents: [doc-mermaid-expert, doc-reviewer, doc-markdown-tester, doc-quality-tracker]
      gates: [p0-clear, diagram-valid, markdown-valid, quality-tracked]
    - id: "5"
      name: curation
      title: Save & Knowledge Curation
      agents: [docs-builder]
      gates: [knowledge-persisted]
    - id: "6"
      name: delivery
      title: Document Sync & Notification
      skills: [import-docs, wework-bot]
agents:
  required:
    - doc-planner
    - docs-retriever
    - doc-impact-analyzer
    - codes-builder
    - doc-architect
    - doc-mermaid-expert
    - doc-reviewer
    - doc-markdown-tester
    - doc-quality-tracker
    - docs-builder
  optional: []
contracts:
  output: shared/agent-output-contract.md
  impact: shared/impact-analysis-contract.md
  evidence: shared/evidence-and-uncertainty.md
---

# generate-document

> Quick reference: [README.md](./README.md)

## Positioning

`generate-document` is the documentation-generation orchestrator. It does not modify code.

### When to use

- A `docs/<feature-name>/` document set exists or needs to be created.
- The user explicitly asks for documentation.
- Progressive refinement of requirements, design, or checklists is needed.

### When NOT to use

- The user wants code implementation (use `implement-code`).
- The user is still clarifying raw requirements (do a quick Q&A first).
- Only a trivial one-line doc fix is needed.

## Input Prerequisites

### P0 (blocking if missing)

- `02_requirement-tasks.md` — user stories, scenarios, preconditions.
- `03_design-document.md` — modules, interfaces, constraints.
- `05_dynamic-checklist.md` — verifiable checklist items.

### P1/P2 (non-blocking)

- `01_requirement-document.md` — background and goals.
- `04_usage-document.md` — UI copy and usage guidance.

## Document Type Matrix

| Type | File | Template Allowed | Generation Mode |
|------|------|------------------|-----------------|
| Requirement Document | `01_requirement-document.md` | Yes | Skeleton + rule constraints |
| Requirement Tasks | `02_requirement-tasks.md` | Yes | Skeleton + rule constraints |
| Design Document | `03_design-document.md` | **No** | **Rules only** |
| Usage Document | `04_usage-document.md` | No | Rules only |
| Dynamic Checklist | `05_dynamic-checklist.md` | **No** | **Rules only** |
| Process Summary | `06_process-summary.md` | — | **Written only by `implement-code`** |
| Project Report | `07_project-report.md` | No | Rules + real change data |

## Commands

### Feature document

```
/generate-document <feature-name>-<description>
```

Example: `/generate-document user-login-phone-otp`

### Project initialization

```
/generate-document init
```

See `rules/init.md` for full specification.

### Weekly report

```
/generate-document weekly [YYYY-MM-DD]
```

After weekly generation, `self-improve.js` runs automatically and appends a "System Self-Improvement Proposals" section.

### From-weekly decomposition

```
/generate-document from-weekly docs/weekly/<week-range>/weekly.md
```

See `rules/from-weekly.md` for full specification.

## Delta Rules (Beyond `document-pipeline` Template)

### 1. Document postscript

Every generated document must append three sections at the end, in this order:

```markdown
## Postscript: Future Planning & Improvements

## Workflow Standardization Review
1. **Repetitive labor identification**: ...
2. **Decision criteria missing**: ...
3. **Information silos**: ...
4. **Feedback loop**: ...

## System Architecture Evolution Thinking
- **A1. Current architecture bottleneck**: ...
- **A2. Next natural evolution node**: ...
- **A3. Risks and rollback plans for evolution**: ...
```

Format details: `skills/self-improving/rules/collection-contract.md`.

### 2. Update-mode shortcuts

| Change Level | Stage 2 (Impact) | Stage 3 (Architecture) | Stage 4 (Generation) |
|--------------|------------------|------------------------|----------------------|
| T1 Micro | Skip (reuse prior) | Skip (reuse prior) | Rewrite changed chapter only |
| T2 Local | Trim (changed point only) | Trim (affected modules only) | Rewrite target + sync downstream entries |
| T3 Scope | Full re-run | Full re-run | Full cascade refresh |

- T1/T2 must not trigger full-project impact rescans.
- Change-level downgrading to save time is prohibited.

### 3. Weekly self-improvement trigger

The `weekly` command must trigger two self-improvement flows after Stage 6:

1. **Execution-memory analysis** (legacy): `node scripts/self-improve.js --since <week-start> --output docs/weekly/<week>/self-improve-proposal.md`
2. **Per-document reflection aggregation** (new): invoke `self-improving` skill to collect `Workflow Standardization Review` and `System Architecture Evolution Thinking` from all feature documents, producing `docs/weekly/<week>/self-improvement-aggregate.md`.

`weekly-analyzer` consumes the aggregate when writing weekly report §5.2 and §5.3.

## Block / Abort Thresholds

| # | Scenario | Degradable? |
|---|----------|-------------|
| H1 | Feature name unparseable and no reasonable default | No |
| H2 | P0 section lacks upstream source and cannot be downgraded to "pending" | No |
| H3 | Same request points to two incompatible feature domains | No |
| H4 | `from-weekly`: weekly invalid or has no actionable items | No |
| H5 | `API_X_TOKEN` missing | Yes (skip sync, notify still sent) |

On abort: persist → sync (skip on H5) → notify → fallback.

## Stop Conditions

Generate a blocking `06_process-summary.md` when:

- P0 prerequisite documents are missing.
- Impact chain cannot be closed.
- Document P0 failures cannot self-repair within 1 round.
- All modules are blocked.

Blocking summary format: record block reason and artifacts → write summary → write block status → `import-docs` + `wework-bot` block notification.

## Supporting Files

```
.claude/skills/generate-document/
├── SKILL.md              # Entry + manifest (this file)
├── README.md             # Quick start + command cheat sheet
├── checklist.md          # Checklist index
├── checklists/           # Per-document-type validation checklists
├── rules/                # Per-document-type rules + command specs
│   ├── workflow.md
│   ├── orchestration.md
│   ├── agent-contract.md
│   ├── orchestration-logging.md
│   ├── init.md
│   ├── weekly.md
│   ├── from-weekly.md
│   ├── requirement-document.md
│   ├── requirement-tasks.md
│   ├── design-document.md
│   ├── usage-document.md
│   ├── dynamic-checklist.md
│   ├── project-report.md
│   ├── project-basics.md
│   ├── weekly-report.md
│   ├── general-document.md
│   ├── coding-standard.md
│   └── code-structure.md
├── templates/            # Skeleton templates (disabled for 03/05)
└── scripts/              # Automation utilities
    ├── validate-agent-contracts.js
    ├── append-key-node.js
    ├── collect-weekly-kpi.js
    ├── collect-weekly-logs.js
    ├── draft-weekly-report.js
    ├── execution-memory.js
    ├── log-agent-run.js
    ├── log-key-node.js
    ├── log-orchestration.js
    ├── natural-week.js
    └── self-improve.js
```
