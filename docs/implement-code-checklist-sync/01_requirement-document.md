# implement-code-checklist-sync

> **Document Version**: v1.0 | **Last Updated**: 2026-05-02 | **Maintainer**: kimi-k2.6 | **Tool**: Claude Code
>
> **Related Documents**: [Requirement Tasks](./02_requirement-tasks.md) | [Design Document](./03_design-document.md) | [Usage Document](./04_usage-document.md) | [CLAUDE.md](../../CLAUDE.md)

[Feature Overview](#feature-overview) | [User Stories](#user-stories) | [Acceptance Criteria](#acceptance-criteria) | [Feature Details](#feature-details)

---

## Feature Overview

The `implement-code` and `generate-document` skills produce a `05_dynamic-checklist.md` at the start of a feature delivery and a `06_process-summary.md` at the end. In the `项目初始化` feature, the 05 checklist remained at 0% completion (all items "pending check") while 06 and 07 claimed all P0 items passed. This breaks the single-source-of-truth principle and misleads downstream readers. This feature adds a mandatory, automatable 05 status write-back step to the `implement-code` process summary rules and extends the same guarantee to `generate-document init` closures.

**Scope**: Modify `.claude/skills/implement-code/rules/process-summary.md` and `.claude/skills/generate-document/rules/init.md` to enforce 05 write-back. Optionally provide a helper script.

**Non-goals**: Changing the 05 document structure, adding new checklist items, or modifying the 06/07 formats.

- 🎯 **Goal**: 05 checklist status always reflects the final verification state
- ⚡ **Impact**: Eliminates sync gaps between checklist and process summary
- 📖 **Clarity**: Write-back is mandatory, not optional, with explicit verification

---

## User Stories and Feature Requirements

**Priority**: 🔴 P0 | 🟡 P1 | 🟢 P2

**One user story corresponds to one `docs/<feature-name>/` numbered set (01–05, 07).**

| User Story | Acceptance Criteria | Process-Generated Documents | Output Smart Documents |
|------------|---------------------|----------------------------|------------------------|
| 🔴 As a process maintainer, I want the 05 dynamic checklist to be automatically updated with final verification results during the process summary stage, so that it remains the single source of truth for feature readiness.
<br/><br/>**Main Operation Scenarios**:<br/>- implement-code completion updates 05 to match Gate B results<br/>- generate-document init completion updates 05 to match final verification<br/>- Cross-skill delivery (generate-document docs + implement-code code) syncs 05 after both stages | 1. `process-summary.md` rule explicitly mandates 05 write-back before 06 is considered complete (P0)<br/>2. `init.md` rule explicitly mandates 05 write-back before init closure (P0)<br/>3. Write-back updates status icons (✅/❌/⏳) and adds evidence links (P0)<br/>4. A verification script or check ensures 05 and 06 statuses are consistent (P1)<br/>5. Inconsistent 05/06 triggers a block or warning before wework-bot notification (P1) | [Requirement Tasks](./02_requirement-tasks.md)<br/>[Design Document](./03_design-document.md)<br/>[Project Report](./07_project-report.md) | [Generate Document Skill](../../.claude/skills/generate-document/SKILL.md)<br/>[Implement Code Skill](../../.claude/skills/implement-code/SKILL.md)<br/>[Requirement Document Specification](../../.claude/skills/generate-document/rules/requirement-document.md) |

---

## Document Specifications

- One numbered set corresponds to one user story
- Anti-hallucination: content that cannot be determined from repository facts/upstream write `> Pending confirmation (reason: …)`

---

## Acceptance Criteria

### P0 — Core (cannot release without)

1. `implement-code/rules/process-summary.md` mandates 05 write-back as a hard gate before stage completion
2. `generate-document/rules/init.md` mandates 05 write-back as a hard gate before init closure
3. Write-back updates status column and adds verification evidence (date, stage, result)
4. Existing 06/07 generation rules remain unchanged except for the new gate

### P1 — Important (recommended)

5. A consistency check script verifies 05 status matches 06 verification table
6. Inconsistency blocks or warns before `wework-bot` notification
7. Write-back is idempotent (re-running does not corrupt 05)

### P2 — Nice-to-have

8. Auto-generate a "diff" section in 05 showing what changed during the delivery

---

## Feature Details

### Mandatory 05 Write-Back in implement-code

- **Description**: Stage 7 (process summary) must not mark complete until 05 status column is updated to reflect Gate A and Gate B results.
- **Boundaries**: Only updates status and evidence; does not add/remove checklist items.
- **Value**: Closes the gap between dynamic checklist and process summary.

### Mandatory 05 Write-Back in generate-document init

- **Description**: After `generate-document init` produces 01-07, the final verification step must write back 05 statuses to reflect actual document quality checks.
- **Boundaries**: Same as above; only status and evidence updates.
- **Value**: Prevents init-generated docs from leaving 05 at template defaults.

### Consistency Verification

- **Description**: A script or agent checks that every P0 item in 05 marked ✅ has a matching ✅ in 06, and every ❌ in 06 is reflected in 05.
- **Boundaries**: Does not auto-fix mismatches; reports them for human review.
- **Value**: Catches write-back omissions before notification.

---

## Usage Scenario Examples

### Scenario 1: implement-code completion with 05 sync

- **Background**: Feature implementation passes Gate B; all P0 items verified.
- **Operation**: Process summary stage runs.
- **Result**: 05 checklist statuses updated to ✅ with evidence links; 06 verification table matches 05.
- 📋 **Verification**: Open 05 and 06 side-by-side; P0 counts match.

### Scenario 2: generate-document init with 05 sync

- **Background**: `generate-document init` produces project initialization docs.
- **Operation**: Init closure stage runs.
- **Result**: 05 statuses updated from template defaults (⏳) to actual verification results (✅).
- 📋 **Verification**: `docs/项目初始化/05_动态检查清单.md` shows updated statuses.

### Scenario 3: Inconsistency detected and blocked

- **Background**: A manual edit causes 05 and 06 to drift.
- **Operation**: Consistency check runs before wework-bot notification.
- **Result**: Block or warning issued; wework-bot notification delayed until resolved.
- 📋 **Verification**: Console shows mismatch details; 05/06 divergence is explicit.

## Postscript: Future Planning & Improvements

- Consider generalizing the consistency check into a shared `.claude/scripts/lib/` module for reuse by all skills.
- Evaluate auto-generating 05 from 06 verification table to eliminate manual write-back entirely.
