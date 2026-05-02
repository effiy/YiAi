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

# Project Basics Specification

> Constrains `/generate-document init` generated project base files and `docs/project-init/` full document numbered set.

## Re-runnable Update Strategy (P0)

1. **Prioritize factual updates**: tech stack, directories, commands, entries, etc. must be refreshed
2. **Preserve human supplements**: team conventions/experience沉淀, if not conflicting with facts keep them
3. **Conflict annotation**: `> TBD (reason: …; recommend following code)` + evidence path
4. **Observable updates**: update header time, `06_process-summary.md` records round summary
5. **Sentinel block safe rewrite**: `<!-- AUTO-GENERATED:BEGIN -->...<!-- AUTO-GENERATED:END -->` sections can be rewritten, content outside blocks is preserved

## File List

### A. Project Base Files (10)

| File | Responsibility | Grounding Source |
|------|---------------|------------------|
| `CLAUDE.md` | Behavioral guidelines entry | `shared/behavioral-guidelines.md` + project supplements |
| `README.md` | Overview and quick start | `package.json` / `index.html` + directories |
| `docs/architecture.md` | Architecture conventions | directories + core entries |
| `docs/changelog.md` | Changelog | `git log` |
| `docs/devops.md` | Build/deploy/ops | build config |
| `docs/network.md` | Network request conventions | network code + API wrappers |
| `docs/state-management.md` | State management conventions | state implementation + persistence |
| `docs/FAQ.md` | FAQ and self-healing | project Q&A + agent memory |
| `docs/auth.md` | Auth scheme | auth code + permission config |
| `docs/security.md` | Security policy | security code + dependency audit |

### B. Full Document Numbered Set (`docs/project-init/`, 7)

01-05 per corresponding `rules/<type>.md` generation; 06 written by init itself; 07 per `rules/project-report.md` generation.

## General Generation Rules (P0)

1. **Anti-hallucination**: content must come from code scan and file reads, do not fabricate
2. **Uncertain annotation**: `> TBD (reason: …)`
3. **Version info real**: maintainer fills model name, tool fills Claude Code / Cursor
4. **Relative paths**
5. **01-07 per 5-step workflow**: feature name = "Project Init"

## Per-File Mandatory Chapters

| File | Mandatory Chapters (in order) |
|------|------------------------------|
| `CLAUDE.md` | Tech stack → Project structure → Coding standard → Prohibitions → Build/run → Key files → Doc system |
| `README.md` | Project name/desc → Intro → Tech stack table → Quick start → Directory structure → Core architecture → Doc table → Contributing → License |
| `architecture.md` | Directory organization → Placement rules → Core architecture patterns → Module structure → Coding standard → Implementation order |
| `changelog.md` | [Keep a Changelog](https://keepachangelog.com) format; feat→new, fix→fix, refactor→change, remove→remove |
| `devops.md` | Build → Deploy → Ops → Environment requirements |
| `network.md` | Request lib → Wrapper entry → BaseURL → Header/auth → Error handling → Common issues |
| `state-management.md` | State categories → Container entry → Read/write boundaries → Persistence → Network collaboration → Common issues |
| `FAQ.md` | Troubleshooting index → Problem categories → Self-healing reference. **Prohibit fixed examples, must infer from project** |
| `auth.md` | Auth architecture → Auth flow → Authz flow → Token management → Self-check rules → No-auth scenarios. If no code keep structure and mark "TBD" |
| `security.md` | Security architecture → Threat model → Check rules → Typical failures → Dependency audit. If no code keep structure and mark "TBD" |

**CLAUDE.md fixed first two lines** (do not modify): `Behavioral guidelines see .claude/shared/behavioral-guidelines.md` and `Project architecture conventions see docs/architecture.md`.

All paths and commands must actually exist.

## 06 Process Summary (init exception)

Implementation overview → process → file list → verification results (P0/P1/P2) → pending items → follow-up suggestions

## Quality Check

> See [checklists/project-basics.md](../checklists/project-basics.md)
