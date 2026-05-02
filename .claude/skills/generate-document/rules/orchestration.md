---
paths:
  - "skills/generate-document/rules/orchestration.md"
  - "docs/*/01_requirement-document.md"
  - "docs/*/02_requirement-tasks.md"
  - "docs/*/03_design-document.md"
  - "docs/*/04_usage-document.md"
  - "docs/*/05_dynamic-checklist.md"
  - "docs/*/07_project-report.md"
---

# Orchestration and Stage Contract Specification

> Core principles, interruption thresholds, and error degradation follow `../SKILL.md` 9 core principles; this file only carries **stage state machine** and **stage-specific behavior**. Agent contracts see `agent-contract.md`; logs see `orchestration-logging.md`.

## 1. Important Constraints (P0)

- **This skill is only responsible for document generation, not modifying code content**
- **Execute to completion in one go whenever possible**: Only interrupt when SKILL.md principle #9 threshold is triggered
- **When human intervention is required, must push via `wework-bot`**: Do not verbally inform

## 2. Stage State Machine

### 2.1 New Mode

| Stage | Name | Goal | Unlock Condition |
|-------|------|------|------------------|
| 0 | Adaptive Planning | Invoke `doc-planner` to generate execution plan | Execution memory has been read, plan has been output (or annotated "skipped") |
| 1 | Parsing + Specification Retrieval | Parse feature name, invoke `docs-retriever` | Feature name / init can be located, specification list has been returned |
| 2 | Upstream Grounding + Impact Analysis | Read upstream documents, `doc-impact-analyzer` impact chain closure (init: scan project code and config) | Fact-source mapping complete, impact chain written into document |
| 3 | Expert Generation | `codes-builder` + `doc-architect` (init: infer architecture pattern) | Module division, interface specifications confirmed |
| 4 | Per-Document Generation + Self-Check | Generate documents according to specifications; three-layer review gate + `doc-quality-tracker` | 01-05, 07 generated, gate passed |
| 5 | Save + Knowledge Curation + Memory Persistence | Save documents, `docs-builder` curate knowledge, **`execution-memory.js` write this session's record**; verify every document ends with Workflow Standardization Review + System Architecture Evolution Thinking | Documents saved, execution memory appended, self-improvement sections present |
| 6 | Document Sync and Notification + Self-Improvement | **`import-docs` first, then `wework-bot`**; `weekly` command triggers `self-improve.js` **and** `self-improving` aggregate | import-docs recorded real result, wework-bot sent, weekly contains self-improvement proposal + aggregate |

### 2.2 Update Mode (Jump by Change Level)

Update mode determines stage execution strategy based on the change level (T1/T2/T3) determined in Step 1:

| Change Level | Stage 1 | Stage 2 | Stage 3 | Stage 4 | Stage 5 |
|--------------|---------|---------|---------|---------|---------|
| **T1 Minor** | Detect diff + reuse specs | **Skip** (reuse last impact analysis) | **Skip** (architecture unchanged) | Rewrite changed chapters of target document | Incremental curation |
| **T2 Partial** | Detect diff + reuse specs | **Trimmed** (only analyze impact of change points) | **Trimmed** (only adjust affected modules) | Rewrite target document + sync downstream corresponding entries | Incremental curation |
| **T3 Scope** | Detect diff + spec retrieval | Full impact analysis | Full expert generation | Full cascade refresh | Full curation |

**Update mode jump rules**:
- T1 change: Stages 2-3 directly marked as "reuse/skip", must not re-invoke `doc-impact-analyzer` / `codes-builder` / `doc-architect`
- T2 change: Stages 2-3 only analyze local impact of change points, must not do full-project rescan
- T3 change: Same as new mode, full execution
- **Level determination must not be downgraded**: If user input clearly involves feature boundary changes, must handle as T3, must not downgrade to save time
- **Specification reuse**: In update mode, if document type is unchanged, Stage 1 may reuse the specification set returned by last `docs-retriever`, only supplementing new specifications
- **Smart trimming (based on planner)**: If `doc-planner` historical data shows that similar features have never triggered stage 2/3 blocking or impact chain issues, and this round's change is clearly T1/T2, may annotate "fast mode" in orchestration logs, trimming stages 2-3 invocation scope, but stage 4 review must not be trimmed

## 3. Blocking Points

- Feature name cannot be parsed
- Specification retrieval fails and cannot be degraded
- Impact chain has unclosed blocking dependency
- Agent invocation fails and no fallback exists
- Document P0 failure and cannot self-repair

When stopping, handle per SKILL.md principle #9: disk write → sync → notify → fallback.

## 4. wework-bot Notification Differences

> Mandatory requirements see SKILL.md principles #7/#9.

- **init success**: `📋 Type` fill "Project Initialization"
- **Update mode**: `🎯 Conclusion` reflect "Update (T1/T2/T3)"; `📦 Artifacts` note "Update N / Keep N / Rewrite chapter M"; T1 update must note "only changed chapters", T2 must note "partial sync"

## 5. Skill / Agent Dispatch

> Agent contract details see `agent-contract.md`.

| Type | Name | Purpose |
|------|------|---------|
| Skill | `import-docs` / `wework-bot` | Stage 6 sync and notification |
| Agent | `docs-retriever` | Stage 1 specification retrieval |
| Agent | `doc-impact-analyzer` | Stage 2 impact chain analysis |
| Agent | `codes-builder` / `doc-architect` | Stage 3 architecture design |
| Agent | `doc-mermaid-expert` / `doc-reviewer` / `doc-markdown-tester` / `doc-quality-tracker` | Stage 4 review and statistics |
| Agent | `docs-builder` | Stage 5 knowledge curation |

## 6. Agent Invocation Gate

> SKILL.md principle #4 defines unified requirements. This section supplements stage binding.

- **Before Stage 1 exit**: `docs-retriever` validation passed
- **Before Stage 2 exit**: `doc-impact-analyzer` validation passed
- **Before Stage 3 exit**: `doc-architect` validation passed

Must not mark complete or enter next stage if not passed (blocking/degradation flow excepted).

Validation script:
```bash
node skills/implement-code/scripts/validate-agent-output.js --agent <agent-name> --text "<output>"
```

## 7. Orchestration Session Logs

> See `orchestration-logging.md` for details.

1. Append log immediately after every skill/agent/MCP/memory/shared interaction
2. Tool: `node scripts/log-orchestration.js` (parameters see `orchestration-logging.md` §1.3)
3. Blocking fallback: Still must complete logs for occurred interactions before ending

## 8. Execution Memory (Stage 5 Mandatory)

After each feature document execution completes, after saving documents in stage 5 must invoke `execution-memory.js` to write this session's record:

```bash
node skills/generate-document/scripts/execution-memory.js write /tmp/session-<feature>.json
```

Record content must include: feature fingerprint, actual change level, invoked agent list, quality issues (P0/P1/P2), bad cases, whether blocked.

## 9. Self-Improvement Trigger (weekly Command)

`weekly` command after stage 6 completes, must automatically trigger two flows:

1. **Execution-memory analysis**:
   ```bash
   node skills/generate-document/scripts/self-improve.js --since <this Monday's date> --output docs/weekly/<week>/self-improve-proposal.md
   ```
   Output appended to the end of weekly report as "System Self-Improvement Proposal" section.

2. **Per-document reflection aggregation** (`self-improving` skill):
   ```bash
   node skills/self-improving/scripts/collect-self-improvement.js --week <this Monday's date> --output docs/weekly/<week>/self-improvement-aggregate.md
   ```
   `weekly-analyzer` consumes this aggregate for weekly report §5.2 and §5.3.
