# Orchestration and Stage Contract Spec

> Stage numbers, names, and entry/exit conditions are authoritative in this file and `../SKILL.md`; other rule files must not redefine stage mappings.

---

## 1. Stage State Machine (Authoritative)

| Stage | Name | Goal | Unlock Condition |
|-------|------|------|------------------|
| 0 | Doc-driven | Parse feature name, pre-check documents, complete grounding and probe checks | P0 docs complete, MCP availability declared |
| 1 | Test-first | Complete minimum viable test in real scenario and fill out test skeleton | Main scenario MVP passed on real entry with retained evidence, scene anchors complete, `data-testid` coverage complete |
| 2 | Dynamic check gate | Verify all P0 items on prototype page | All P0 passed and written back to `05_dynamic-checklist.md` |
| 3 | Module pre-check | Complete environment pre-check and full-project impact-chain closure analysis | Pre-check list fully passed, dependencies closed |
| 4 | Write project code | Implement module by module and verify module by module | Module implementation complete, lint/regression/impact-chain regression records complete |
| 5 | Code review | Execute code-review and mock leak check | No P0 review issues |
| 6 | Smoke test | AI automatically executes main-flow full-chain smoke and writes back status | AI automation main-flow smoke passed, all P0 passed and written back to `05` |
| 7 | Process summary | Generate `06_process-summary.md` (must include §8 Workflow Standardization Review + §9 System Architecture Evolution Thinking) and write back feature document status | Summary write complete, self-improvement sections present, status write-back complete, dynamic checklist final gate passed |
| 8 | Document sync and notification | Sync `docs` and send notification; optional: trigger `self-improving collect` to harvest new reflection sections | `import-docs` executed or skip reason recorded, wework-bot sent by end type |

---

## 2. Input Prerequisites

### 2.1 Default Input

- `{feature-name}`: corresponds to `docs/<feature-name>/`
- `{document-set-path}`: default `docs/<feature-name>/`

When unparseable, first write to `docs/99_agent-runs/<YYYYMMDD-HHMMSS>_implement-code.md` to record reason and recovery steps, then request supplementation.

### 2.2 Minimum Document Requirements

| File | Level | Purpose |
|------|-------|---------|
| `02_requirement-tasks.md` | P0 | User stories, scenarios and preconditions |
| `03_design-document.md` | P0 | Modules, interfaces, file paths and implementation constraints |
| `05_dynamic-checklist.md` | P0 | All pending verification check items |
| `01_requirement-document.md` | P1 | Background and goal supplement |
| `04_usage-document.md` | P2 | Auxiliary UI copy |

When P0 documents are missing: record missing → stop entering stage 1 → generate block summary → prompt to run `generate-document`.

### 2.3 Git Feature Branch (Mandatory)

When the repository is git, must use `feat/<feature-name>` branch; `git switch` before code changes. Continuing on wrong branch is prohibited; when unable to switch, treat as block and notify.

### 2.4 Execute to Completion in One Shot

By default do not frequently ask questions; missing information write "to be confirmed" and continue. When human intervention is needed, first land fallback record, then `wework-bot` push.

---

## 3. Stage 0 Details

### 3.1 Document Grounding Output

Must extract at least: user stories (scenario name + preconditions + operation steps + expected results), implementation constraints (modules + interfaces + state management + existing code paths + impact chain), check item mapping (scenario → P0/P1/P2 list).

### 3.2 Skill / Agent Dispatch

| Type | Name | Purpose |
|------|------|---------|
| Skill | `find-skills` | Declare and discover skills to use |
| Skill | `find-agents` | Discover and dispatch agents |
| Skill | `e2e-testing` | Stage 1 produces test skeleton |
| Skill | `verification-loop` | Stage 3/5 static pre-check and test execution |
| Skill | `code-review` | Stage 5 real code review |
| Skill | `search-first` | External dependency selection (as needed) |
| Agent | `test-page-builder` | Stage 1 generates test prototype page |
| Agent | `codes-builder` | Architecture confirmation and implementation strategy validation |
| Agent | `code-reviewer` | Security-related scenarios (security audit dimension) |
| Agent | `codes-retriever` | Code context retrieval |
| Agent | `code-impl-reporter` | Stage 7 generates implementation summary |

### 3.3 MCP Probe and Degradation

Before entering stage 1, must complete:

| MCP Tool | Minimum Probe | Fallback Plan | Blocking |
|---------|---------------|---------------|----------|
| `browser` | Open `about:blank` | Equivalent scriptable automation + human confirmation | No |
| Filesystem capability | Reuse document read results | Use local read/write tools | No |
| Necessary tool with no fallback | Minimum viable probe | None | Yes |

Silent degradation prohibited. All degradation recorded to `06_process-summary.md`. When probe/degradation/gate evidence is missing, treat as "gate failure".

### 3.4 Scenario–Checklist Coverage Pre-Check

Before writing tests and passing gates, explicitly verify whether scenarios in `02_requirement-tasks.md` all have executable P0 check items in `05_dynamic-checklist.md`:

1. List all user stories/scenarios from `02`
2. List all P0 check items from `05`
3. Build table: scenario → covered P0 items → gap description ("none" or "to supplement" + reason)
4. Enter stage 1: "to supplement" may exist but must record reason in `05` or `docs/99_agent-runs/`
5. Enter stage 2: all P0 scenarios must have at least one `05` mapping, or be marked N/A with reason written

---

## 4. Stage Entry/Exit Conditions

| Stage | Enter | Exit |
|-------|-------|------|
| 1 | Stage 0 complete | MVP passed on real entry + evidence retained + test artifacts under `tests/` |
| 2 | Stage 1 complete | All P0 passed, status written back to `05` |
| 3 | Stage 2 complete | Environment pre-check + impact chain closed + coding pre-check all passed |
| 4 | Stage 3 complete | Module implementation + per-module verification + impact-chain regression based on real diff complete |
| 5 | Stage 4 complete | No P0 review issues, mock leak check passed |
| 6 | Stage 5 complete | AI auto main-flow smoke passed, all P0 passed and written back |
| 7 | Stage 6 complete | Summary write complete + status write-back complete + dynamic checklist final gate passed |
| 8 | Stage 7 complete | import-docs executed + wework-bot sent by end type |

Stage 7 block exit condition: only needs to satisfy summary write + status write-back + gate conclusion (even if not passed).

---

## 5. Block Points

Must stop when: feature name/path cannot be located / cannot ready branch on `feat/<feature-name>` / P0 documents missing / necessary MCP unavailable with no fallback / stage 2 or 6 reaches fix上限 / Gate A incomplete yet code is written / Gate B not passed / gate not executed/missing evidence/skipped / all modules blocked.

On stop: output block reason → record current stage and artifacts → generate block summary → write back status → `import-docs` → `wework-bot` block notification. When notification send fails, write to `06_process-summary.md` or `docs/99_agent-runs/`.

---

## 6. Orchestration Session Logs (Mandatory)

skill/agent/MCP/memory/shared interactions, append to `docs/weekly/<YYYY-MM-DD>~<YYYY-MM-DD>/logs.md` immediately after each round:

1. **Trigger timing**: after each round of invocation completes
2. **Tool**: `node .claude/skills/generate-document/scripts/log-orchestration.js` (parameters see `../SKILL.md`)
3. **Record structure**: operation scenario + conversation summary; optional `--case good|bad`, `--tags`, `--lesson`. Empty placeholders prohibited
4. **Block补齐**: when interrupted mid-way, still must补齐 already occurred interaction logs

---

## 7. Key Node Records (Recommended)

Stage switches, gate conclusions, notification results and other milestones, recommended to append to `docs/weekly/<YYYY-MM-DD>~<YYYY-MM-DD>/key-notes.md`: `node .claude/skills/generate-document/scripts/log-key-node.js`. Complements §6, cannot replace §6.
