# Path and Link Conventions

This document unifies path notation in the `.claude` system to avoid obsolete directory models and broken links.

## Stable Entry Points

- Skills directory: `.claude/skills/<skill-name>/`
- Skills source of truth: `.claude/skills/<skill-name>/SKILL.md`
- Agents directory: `.claude/agents/<agent-name>.md`
- Commands directory: `.claude/commands/<command-name>.md`
- Evaluation examples: `.claude/eval/skills/<skill>.md`, `eval/agents/<agent>.md` (user stories and sample inputs; first phase `skills/wework-bot.md`, `agents/message-pusher.md`, not skill source of truth)

## Obsolete Paths (Prohibited)

The following notations are deprecated and must not appear in any rules, templates, or READMEs:

- `.claude/skills/generate-document.md`
- `.claude/rules/...`
- `.claude/templates/...`
- `.claude/skills/checklist/...`

## Recommended Notation

### Referencing `.claude` from `docs/` documents

When back-linking from documents at different depths under `docs/` to `.claude`, use a relative path from the current file to the repository root:

- **2 levels deep** (e.g. `docs/<feature-name>/`): `../../.claude/skills/generate-document/SKILL.md`
- **3 levels deep** (e.g. `docs/weekly/<natural-week>/`): `../../../.claude/skills/generate-document/SKILL.md`
- **4 levels deep** (e.g. deeper nesting): add `../` per level

Examples:

- `../../.claude/skills/generate-document/SKILL.md` (2 levels)
- `../../.claude/skills/generate-document/rules/requirement-document.md` (2 levels)
- `../../../.claude/skills/generate-document/SKILL.md` (3 levels, inside weekly directory)

### Fallback Path

When a skill cannot write the target artifact due to missing parameters, undeterminable target directory, or missing prerequisite materials, it must still write to:

- `docs/99_agent-runs/<YYYYMMDD-HHMMSS>_<skill-name>.md`

### Internal Cross-References Within `.claude`

Prefer relative paths based on the current file's location that can be directly resolved, without creating alias directories.

## Link Governance Rules

- Only link to skill, agent, rule, template, checklist, and eval example documents that actually exist in the repository.
- If a capability has no dedicated skill or agent entry, explicitly write "no dedicated entry provided" instead of fabricating a name.
- After directory structure changes, perform a full-repository `.claude/` link regression search.
