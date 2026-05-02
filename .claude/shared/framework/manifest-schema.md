---
paths:
  - "shared/framework/manifest-schema.md"
---

# Intent-Pipeline Protocol (IPP) — Manifest Schema

This document defines the single source of truth for all skill and agent manifests in this repository. Every `SKILL.md` and `agents/<name>.md` file MUST conform to this schema. The Contract Compiler (`scripts/compile-manifests.js`) validates all manifests against this schema.

## Philosophy

- **Data over prose**: Orchestration (stages, gates, agents) is declared as structured data in YAML frontmatter. Markdown body provides human-readable rationale and edge-case handling.
- **Single source of truth**: An agent's contract lives only in its own manifest. Skills reference agents by name; the compiler validates.
- **Inheritance over duplication**: Common lifecycle patterns (logging, notification, severity gates) are defined once in lifecycle templates and inherited by skills.

---

## Skill Manifest (`SKILL.md`)

### Required Frontmatter

```yaml
---
name: string                    # Machine identifier (kebab-case). Must match directory name.
description: string             # One-line summary for discovery and indexing.
user_invocable: boolean         # true = exposed as a slash command; false = internal only.
lifecycle: string               # Name of inherited lifecycle template (see lifecycle-templates/).
pipeline:                       # Declarative stage graph.
  stages:
    - id: string                # Stage identifier ("0", "1", "2a", etc.).
      name: string              # Machine name (kebab-case).
      title: string             # Human-readable title.
      agents: [string]          # Agents invoked in this stage.
      skills: [string]          # Sub-skills invoked in this stage (optional).
      gates: [string]           # Gate IDs that must pass before stage exit.
      optional: boolean         # If true, stage may be skipped under declared conditions.
      parallel: boolean         # If true, agents in this stage may run in parallel.
      delta_rules: string       # Path to markdown file with stage-specific rules (relative to SKILL.md).
agents:
  required: [string]            # Agents that must exist in agents/ directory.
  optional: [string]            # Agents that may be conditionally invoked.
contracts:
  output: string                # Path to agent output contract (usually shared/agent-output-contract.md).
  impact: string                # Path to impact analysis contract (optional).
  evidence: string              # Path to evidence/uncertainty contract (optional).
---
```

### Constraints

- Every agent in `pipeline.*.agents` must appear in either `agents.required` or `agents.optional`.
- Every gate in `pipeline.*.gates` must be declared in at least one agent's `contract.gates_provided`.
- `lifecycle` must reference an existing file in `shared/framework/lifecycle-templates/`.
- `id` values within a pipeline must be unique.

### Body Content

The markdown body below the frontmatter is documentation, not logic. It should contain:

1. **Positioning** — When to use / not use this skill.
2. **Input prerequisites** — Required documents, environment variables, or state.
3. **Delta rules** — Any behavior that deviates from the inherited lifecycle template.
4. **Stop conditions** — When and how the skill halts with a blocking summary.
5. **Directory layout** — Where supporting files (rules, scripts, templates) live.

Do NOT duplicate stage transitions, gate mechanics, or notification rules that are already covered by the inherited lifecycle template.

---

## Agent Manifest (`agents/<name>.md`)

### Required Frontmatter

```yaml
---
name: string                    # Machine identifier (kebab-case). Must match filename.
description: string             # One-line role summary.
role: string                    # Human-readable role title.
user_story: string              # "As a [role], I want [goal] so that [benefit]."
triggers: [string]              # Events or stage IDs that trigger this agent.
tools: [string]                 # Claude tools used (Read, Write, Grep, Glob, Bash, etc.).
contract:
  required_answers: [string]    # Question IDs that must be answered (e.g., [Q1, Q2, Q3]).
  artifacts:                    # Structured outputs this agent guarantees.
    - name: string
      type: string              # e.g., "array", "object", "boolean", "string"
      required: boolean
  gates_provided: [string]      # Gate IDs this agent can satisfy.
  skip_conditions: [string]     # Human-readable conditions under which this agent may be skipped.
---
```

### Constraints

- `name` must match the filename without `.md`.
- Every `gates_provided` ID must be unique across all agents (the compiler enforces this).
- `required_answers` must not be empty.

### Body Content

The markdown body should contain:

1. **Core positioning** — What this agent does and what it does NOT do.
2. **Workflow** — Step-by-step execution guide for Claude.
3. **Required questions** — The full text of each required question, mapped to the IDs in frontmatter.
4. **Constraints** — Hard limits (e.g., "do not modify code files").
5. **Output contract appendix** — A JSON fenced code block appended to every output, conforming to `shared/agent-output-contract.md`.

---

## Gate Taxonomy

Gates are boolean checkpoints. They are declared by stages and satisfied by agents.

| Gate ID | Description |
|---------|-------------|
| `execution-memory-ready` | Execution memory has been read and is non-empty or explicitly marked skipped. |
| `specs-loaded` | Relevant rules, shared contracts, and checklists have been identified. |
| `impact-chain-closed` | Forward and reverse dependencies have been analyzed and documented. |
| `architecture-validated` | Module boundaries, interface specs, and dataflow are confirmed. |
| `p0-clear` | No P0 issues remain in the current stage output. |
| `markdown-valid` | Markdown structure, links, and syntax pass validation. |
| `quality-tracked` | P0/P1/P2 statistics have been recorded. |
| `knowledge-persisted` | Reusable patterns and lessons have been written to memory. |
| `synced` | `import-docs` has completed successfully. |
| `notified` | `wework-bot` has sent the completion/block notification. |
| `tests-defined` | Gate A: test plan and acceptance criteria exist before coding. |
| `smoke-passed` | Gate B: full main-flow smoke test passes after coding. |

New gate IDs may be added, but they must be documented here and claimed by at least one agent's `gates_provided`.

---

## Versioning

Manifest schema version is tracked implicitly by git. When a breaking change is made to this schema (new required fields, renamed keys), all manifests must be updated in the same commit. The Contract Compiler exits with code 1 if any manifest fails schema validation.
