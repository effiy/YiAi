---
paths:
  - "CLAUDE.md"
  - "README.md"
  - "docs/architecture.md"
  - "docs/changelog.md"
  - "docs/devops.md"
  - "docs/network.md"
  - "docs/state-management.md"
  - "docs/FAQ.md"
  - "docs/auth.md"
  - "docs/security.md"
  - "docs/project-init/**/*.md"
---

# Project Initialization (init) Command Specification

> Core principles, interruption thresholds, and notification requirements follow `../SKILL.md`; this file only carries init-specific behavior details.

## Invocation

```bash
/generate-document init
```

## Output List

| Category | Output | Description |
|----------|--------|-------------|
| Project basics (10 files) | `CLAUDE.md`, `README.md`, `docs/architecture.md`, etc. | Repository root or `docs/` |
| Full document numbered set (7 files) | `docs/project-init/01-07` | Contains `06_process-summary.md` (written by init itself) |

## Workflow

1. Scan repository structure: read `package.json` / build config / source directories / git history, etc.
2. Stage 1: Invoke `docs-retriever` to retrieve applicable specifications
3. Stage 2: Scan project code and configuration (init has no impact analysis requirement, skip `doc-impact-analyzer`)
4. Stage 3: Invoke `codes-builder` + `doc-architect` to infer project architecture patterns
5. Stage 4: Generate 10 basic files + `docs/project-init/` 01-07; three-layer review gate + `doc-quality-tracker` statistics
6. Stage 5: Save documents, invoke `docs-builder` to curate knowledge
7. Stage 6: `import-docs` first, then `wework-bot`

## Re-execution (re-init) Update Strategy

### Change Levels (consistent with feature documents)

| Level | Criteria | Handling Strategy |
|-------|----------|-------------------|
| **T1 Minor** | Version bump, dependency update, config tweak, README wording optimization | Rewrite only changed paragraphs, retain manual additions and team conventions |
| **T2 Partial** | New/deleted directories, tech stack component changes, new command entry | Rewrite changed chapters + sync update all associated documents that reference this chapter |
| **T3 Scope** | Architecture pattern changes, project type changes (e.g. frontend → full-stack), build tool replacement | Full cascade refresh |

### re-init General Strategy

| Strategy | Description |
|----------|-------------|
| Prioritize factual updates | Tech stack, directory structure, commands, entries, etc. must be refreshed |
| Retain manual additions | Team conventions / accumulated experience, if already present and not conflicting with facts, retain by default |
| Conflict annotation | When statements conflict with code facts, annotate `> Pending confirmation (reason: …)` |
| Sentinel-block safe rewrite | Paragraphs wrapped in `<!-- AUTO-GENERATED:BEGIN/END -->` may be rewritten; content outside the block is retained |
| Observable update | Record this round's update summary in `06_process-summary.md` (including change level and affected file list) |

## Differences Between init and Feature Documents

| Dimension | `init` | `<feature-name>-description` |
|-----------|--------|------------------------------|
| Feature name | Fixed as "Project Initialization" | User-specified |
| 06_process-summary | Written by init itself | Written by implement-code |
| Output location | 10 files in root + `docs/project-init/` | `docs/<feature-name>/` |
| Update strategy | re-init: refresh facts, retain conventions, mark conflicts as pending | Diff comparison, cascade update, version increment |
