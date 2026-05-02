# `.claude` Directory Overview

The `.claude` directory hosts this repository's Claude / Cursor collaboration layer: command entries, skill definitions, expert agents, and shared standards.

## Directory Responsibilities

| Directory | Purpose | Stable Entry? |
|-----------|---------|---------------|
| `commands/` | Slash Command wrappers; only delegate to skills | Yes |
| `skills/` | Directly invocable skill definitions; `SKILL.md` is the source of truth | Yes |
| `agents/` | Expert agent definitions; own role, I/O, and required questions | Yes |
| `mcp.json` | MCP Server configuration (project-level); bridges SSE endpoints via `mcp-proxy` | Yes |
| `eval/` | Evaluation examples: `eval/skills/`, `eval/agents/` (first phase: wework-bot + message-pusher); not source of truth | No |
| `shared/` | Shared explanatory documents, unifying conventions, paths, and boundary definitions | No |

## Source-of-Truth Rules

1. `commands/*.md` keeps only a one-line entry description; does not carry domain rules.
2. `skills/<name>/SKILL.md` is the behavioral source of truth for that skill.
3. `skills/<name>/README.md` is for quick start, navigation, and index only; does not repeat full rules.
4. `skills/<name>/rules/*.md` defines structural contracts (provided by some skills, not required).
5. `skills/<name>/templates/*.md` provides optional skeletons only; must not override `rules/` (provided by some skills, not required).
6. `skills/<name>/checklists/*.md` defines acceptance items; `checklist.md` serves only as an entry index (provided by some skills, not required).
7. `agents/*.md` describes agent roles only; does not copy the skill's full process.

## Suggested Reading Order

### Document Generation Pipeline

1. `skills/generate-document/SKILL.md`
2. `skills/generate-document/README.md`
3. `shared/document-contracts.md`
4. `shared/evidence-and-uncertainty.md` (shared by generate-document / implement-code: anti-hallucination, admissibility, self-improvement and verifiable next steps in `06`)
5. `shared/impact-analysis-contract.md`
6. `shared/path-conventions.md`
7. `shared/agent-skill-boundaries.md`

Completion stage fixed order: first invoke `skills/import-docs/SKILL.md` to sync `docs`, then invoke `skills/wework-bot/SKILL.md` to send completion notification with real sync numbers.

### Document Import Pipeline

1. `skills/import-docs/SKILL.md`
2. `skills/import-docs/README.md`
3. `skills/import-docs/rules/import-contract.md`
4. `skills/import-docs/scripts/import-docs.js`

### Notification and Observation Pipeline

1. `skills/wework-bot/SKILL.md`
2. `skills/wework-bot/README.md`
3. `skills/wework-bot/rules/message-contract.md`
4. `skills/wework-bot/config.example.json` (routing and webhook structure example; locally copy `config.json` from this and fill in real addresses)
5. `skills/wework-bot/scripts/send-message.js`
6. Long-process push copy strategy and anti-hallucination check: `shared/message-pusher.md` (Plan first, then draft, then call `send-message.js`)

The repository's `skills/wework-bot/config.json` retains placeholder webhooks only; for local development, copy `config.example.json` to `config.json` and fill in real addresses, or point the `WEWORK_BOT_CONFIG` environment variable to a private path. `API_X_TOKEN` comes **only** from environment variables (not read from config files).

### Skill and Agent Division of Labor

1. `shared/agent-skill-boundaries.md`
2. `skills/find-skills/SKILL.md`
3. `skills/find-agents/SKILL.md`

## MCP Configuration

Project-level MCP Server definitions are in `mcp.json`, bridged via `mcp-proxy` from SSE endpoints to stdio interfaces consumable by Claude Code:

```bash
npx -y mcp-proxy https://api.effiy.cn/mcp
```

`effiy-api` (`https://api.effiy.cn/mcp`) is pre-configured by default, exposing a FastAPI endpoint based on [fastapi_mcp](https://github.com/tadata-org/fastapi_mcp). Claude Code automatically loads available tools on startup.

## Maintenance Conventions

- Do not change top-level naming conventions for `.claude/skills/`, `.claude/agents/`, `.claude/commands/`; add evaluation examples following `.claude/eval/skills/<skill>.md`, `eval/agents/<agent>.md` (see first phase at `eval/skills/wework-bot.md`).
- When adding shared standards, prefer `shared/` to avoid scattering explanatory content across multiple skills/agents.
- When updating path conventions, synchronously check links in `README.md`, `rules/`, `templates/`, `checklists/`.
