# generate-document README

> Behavioral source of truth: [SKILL.md](./SKILL.md); this file keeps only quick-start and command cheat-sheet.

## Quick Start

```bash
/generate-document init                           # Project initialization
/generate-document user-login-phone-otp            # Feature document set
/generate-document weekly                         # This week's weekly report
/generate-document weekly 2026-04-29              # Weekly report for a specific date
/generate-document from-weekly docs/weekly/<natural-week>/weekly.md  # Decompose weekly into full document sets
```

- All commands are idempotent; existing documents are incrementally updated.
- Target directory: `docs/<feature-name>/`, numbered set 01–05, 07 (06 written only by `implement-code`)
- Mandatory at end: `import-docs` (sync) → `wework-bot` (notify); neither may be skipped on interruption or completion.

## Command Cheat Sheet

| Command | Output | First Run | Re-run | Version Handling |
|---------|--------|-----------|--------|------------------|
| `init` | 10 base files + `docs/project-init/01-07` | Create new | Update facts, keep conventions | Header date updated |
| `<feature-name>-<description>` | `docs/<feature-name>/01-05,07` | Create full set | Diff comparison, cascade update | Minor `+1` |
| `weekly [date]` | `docs/weekly/<natural-week>/weekly.md` | Create new | Same-week overwrite update | Minor `+1` |
| `from-weekly <weekly-path>` | Multiple `docs/<feature-name>/` full sets | Create multiple directories | Each directory independently "update if exists" | Each directory independently `+1` |

## Full-Document Type Overview

| Type | File Name | Template | Generation Mode |
|------|-----------|----------|-----------------|
| Requirement Document | `01_requirement-document.md` | ✅ | Skeleton + rule constraints |
| Requirement Tasks | `02_requirement-tasks.md` | ✅ | Skeleton + rule constraints |
| Design Document | `03_design-document.md` | ❌ | **Spec-driven only** |
| Usage Document | `04_usage-document.md` | ❌ | Spec-driven |
| Dynamic Checklist | `05_dynamic-checklist.md` | ❌ | **Spec-driven only** |
| Process Summary | `06_process-summary.md` | — | **Only implement-code writes** |
| Project Report | `07_project-report.md` | ❌ | Spec-driven + real change data |
| Weekly Report | `docs/weekly/<natural-week>/weekly.md` | ❌ | Single document, not a numbered set |

## Source of Truth and Contracts

| Source | Path | Purpose |
|--------|------|---------|
| Behavioral source of truth | `./SKILL.md` | Core principles + workflow + commands |
| Document contracts | `../../shared/document-contracts.md` | Document structure and write-back |
| Impact analysis contract | `../../shared/impact-analysis-contract.md` | Impact chain closure |
| Evidence and anti-hallucination | `../../shared/evidence-and-uncertainty.md` | Fact-source constraints |
| Agent output contract | `../../shared/agent-output-contract.md` | Gate validation |
| Path conventions | `../../shared/path-conventions.md` | Directory and naming |
| Skill/Agent boundaries | `../../shared/agent-skill-boundaries.md` | Responsibility division |

## Directory Navigation

- `SKILL.md`: sole source of truth (9 core principles + commands + workflow entry)
- `rules/`: per-document-type specs + orchestration details
- `templates/`: optional skeletons (03/05 templates disabled)
- `checklists/`: specialized checklists (P0/P1/P2)
- `checklist.md`: checklist entry index
