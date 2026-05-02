---
name: find-agents
description: |
  Discover and recommend parallel-callable agents in .claude/agents/ based on
  document type and task objective. Used when assigning expert agents for document
  generation, review, validation, and other tasks.
user_invocable: true
lifecycle: default-pipeline
---

# find-agents

## Purpose

Discover available agents in the current project's `.claude/agents/` directory, and recommend parallel agent combinations by task type along with each agent's "required questions."

Directory conventions and source of truth: `../../README.md`; for Skill vs Agent boundaries, see `../../shared/agent-skill-boundaries.md`.

## Input

- **Document type**: such as `design document`, `project report`, `dynamic checklist` (required)
- **Task objective**: such as `generate design document`, `review newly generated design document` (required)
- **Upstream context summary**: upstream document path + 3-5 key facts (optional)

## Workflow

1. List all `.md` files in `.claude/agents/` **root directory**
2. Read each file's frontmatter `role` and `triggers` fields
3. Match by document type and task objective, select parallel agent combinations
4. Generate "required questions" for each agent

## Default Agent Mapping

| Trigger Scenario | Recommended Agents |
|------------------|-------------------|
| Before design document generation | `doc-architect` + `codes-builder` + `doc-impact-analyzer` |
| Before project report generation | `code-reviewer` + `docs-retriever` |
| Dynamic checklist E2E scenarios | `code-e2e-tester` |
| Post-save review | `doc-reviewer` + `code-reviewer` + `doc-markdown-tester` |
| Grounding / upstream location | `docs-retriever` |
| Involving security/auth | `code-reviewer` (security audit dimension) |
| Specification retrieval | `docs-retriever` / `codes-retriever` |
| Full-project impact analysis | `doc-impact-analyzer` / `code-impact-analyzer` |
| Quality trend tracking | `doc-quality-tracker` |
| Knowledge curation | `docs-builder` |
| WeChat Work push copywriting, session usage completion, anti-hallucination check | `message-pusher` |
| Mermaid diagram syntax review in Markdown (before generate-document Stage 4 finalization) | `doc-mermaid-expert` |
| implement-code Stage 1 | `codes-retriever` + `code-impact-analyzer` + `codes-builder` |
| implement-code Stage 3/4 | `code-impact-analyzer` + `doc-impact-analyzer` |
| implement-code Stage 4 summary | `code-impl-reporter` + `doc-quality-tracker` + `docs-builder` |

## Output Format

```
Parallel-callable agents:
- <agent name>
  Role: <one sentence>
  Input: <what needs to be provided>
  Output: <expected return>
  Required questions:
    1. <question 1>
    2. <question 2>
```

## Usage Rules

- **No fabrication**: only return agent file names (without `.md`) that truly exist in `.claude/agents/`.
- **Parallel first**: returned agent lists are designed to be called simultaneously by default; no hidden sequential dependencies.
- **Agent returns are candidates only**: final write decisions are made by the caller (e.g., generate-document) per conventions.
