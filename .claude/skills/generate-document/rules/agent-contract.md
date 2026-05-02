---
paths:
  - "skills/generate-document/rules/agent-contract.md"
---

# Agent Invocation Contract

> See `../SKILL.md` #3/#4 for core principles; see `orchestration.md` §6 for stage binding; see `../../shared/agent-output-contract.md` for the output JSON format.

## 1. Command Applicability Matrix

| Agent | Feature Document | init | weekly | from-weekly |
|-------|-----------------|------|--------|-------------|
| `doc-planner` | ✅ Step 0 | — | — | ✅ Step 0 |
| `docs-retriever` | ✅ Step 1 | ✅ Step 1 | — | ✅ Step 1 |
| `doc-impact-analyzer` | ✅ Step 2 | — | — | ✅ Step 2 |
| `codes-builder` | ✅ Step 3 | ✅ Step 3 | — | ✅ Step 3 |
| `doc-architect` | ✅ Step 3 | ✅ Step 3 | — | ✅ Step 3 |
| `doc-mermaid-expert` | ✅ Step 4 | ✅ Step 4 | ✅ Step 4 | ✅ Step 4 |
| `doc-reviewer` | ✅ Step 4 | ✅ Step 4 | ✅ Step 4 | ✅ Step 4 |
| `doc-markdown-tester` | ✅ Step 4 | ✅ Step 4 | ✅ Step 4 | ✅ Step 4 |
| `doc-quality-tracker` | ✅ Step 4 | ✅ Step 4 | ✅ Step 4 | ✅ Step 4 |
| `docs-builder` | ✅ Step 5 | ✅ Step 5 | ✅ Step 5 | ✅ Step 5 |
| `execution-memory`* | ✅ After stage 5 | ✅ After stage 5 | — | ✅ After stage 5 |

> `execution-memory` is a "pseudo agent" (script invocation), with no JSON contract requirement, but must write structured data according to the specification.

## 2. Per-Agent Contract

| Agent | Stage | Responsibility | Adoption Rule | Skip Condition |
|-------|-------|----------------|---------------|----------------|
| `doc-planner` | 0 | Generate adaptive execution plan based on execution memory | Suggested change level and agent strategy must serve as reference input for subsequent steps | May skip when execution memory does not exist or is empty (must annotate) |
| `docs-retriever` | 1 | Retrieve rules/shared/checklists specifications | Returned list must be used for subsequent loading | Empty list may continue (annotate "not returned"), but the call must not be skipped |
| `doc-impact-analyzer` | 2 (only 02/03) | Full-project impact chain closure | Result written to chapter 6 of 02 / chapter 5 of 03 | When not closed, write "Uncovered Risk" and annotate "pending manual confirmation" |
| `codes-builder` | 3 (only 03) | Architecture design and code structure analysis | Conclusion must be adopted into design document | **Must not skip**; failure follows blocking flow |
| `doc-architect` | 3 (only 03) | 5 mandatory questions (Q1 modules, Q2 interfaces, Q3 data flow, Q4 architecture diagram, Q5 convention compatibility) | Module division / interface specifications must be adopted | **Must not skip**; failure follows blocking flow |
| `doc-mermaid-expert` | 4 (before Mermaid document finalization) | Mermaid syntax review and fix | Write back to the same file after fix | May skip if no Mermaid block |
| `doc-reviewer` | 4 (after all document types) | Structure and expression quality review + cross-document consistency check | P0 must be fixed before saving | **Must not skip** |
| `doc-markdown-tester` | 4 | Markdown quality test | — | **Must not skip** |
| `doc-quality-tracker` | 4 | P0/P1/P2 statistics | — | **Must not skip** |
| `docs-builder` | 5 | Knowledge curation | — | **Must not skip** |

## 3. Invocation Order Constraints

1. `doc-planner` must precede `docs-retriever` (Step 0 before Step 1)
2. `doc-mermaid-expert` must precede `doc-reviewer`
3. `doc-impact-analyzer` must precede `codes-builder` / `doc-architect`
4. `codes-builder` and `doc-architect` may run in parallel
5. `execution-memory` write must occur after `docs-builder` and before `import-docs`
6. Stage binding is strictly enforced

## 4. Gate Validation

> SKILL.md principle #4 defines unified requirements.

- Agent output must append a JSON contract appendix block at the end (see `../../shared/agent-output-contract.md`)
- Validate before adoption (at least mandatory question coverage + artifact existence)
- Script: `node skills/implement-code/scripts/validate-agent-output.js --agent <name> --text "<output>"`
- Failure handling: 1st attempt → supplementary retry; 2nd attempt → treat as invocation failure and follow blocking/degradation flow

## 5. Source-of-Truth Index

| Topic | Source of Truth |
|-------|-----------------|
| Impact analysis dimensions | `../../shared/impact-analysis-contract.md` |
| Agent output JSON format | `../../shared/agent-output-contract.md` |
| Skill / Agent boundaries | `../../shared/agent-skill-boundaries.md` |
| Stage binding and gates | `rules/orchestration.md` §6 |
| Per-agent mandatory questions | `../../agents/<name>.md` |
| Execution memory format | Data structure comments in `scripts/execution-memory.js` |
| Self-improvement output | Proposal format in `scripts/self-improve.js` |
