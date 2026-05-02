---
paths:
  - "docs/*/01_requirement-document.md"
---

# Requirement Document Specification

> Upstream/downstream boundary: Requirement document only writes "what to do / what not to do"; implementation details go in `03_design-document.md`; executable verification items go in `05_dynamic-checklist.md`; delivery evidence goes in `07_project-report.md`.

## Document Structure (Strictly Follow)

### 1. Document Header

```markdown
# {feature-name}

> **Document Version**: v1.0 | **Last Updated**: {date} | **Maintainer**: {model name} | **Tool**: {Claude Code / Cursor}
>
> **Related Documents**: [Requirement Tasks](./02_requirement-tasks.md) | [Design Document](./03_design-document.md) | [Usage Document](./04_usage-document.md) | [CLAUDE.md](../../CLAUDE.md)
>

[Feature Overview](#feature-overview) | [User Stories](#user-stories) | [Acceptance Criteria](#acceptance-criteria) | [Feature Details](#feature-details)

---
```

### 2. Feature Overview

- 3-6 sentences describing goals, scope, and non-goals, citing repository facts (directories/entries/constraints), uncertain then annotate `> Pending confirmation (reason: …)`
- 3 core value points: 🎯⚡📖

### 3. User Stories and Feature Requirements (Must Include Table)

**Priority**: 🔴 P0 | 🟡 P1 | 🟢 P2

**One user story corresponds to one `docs/<feature-name>/` numbered set (01–05, 07).**

| User Story | Acceptance Criteria | Process-Generated Documents | Output Smart Documents |
|------------|---------------------|----------------------------|------------------------|
| 🔴 As [role], I want [feature], so that [value]<br/><br/>**Main Operation Scenarios**:<br/>- {scenario 1 description}<br/>- {scenario 2 description}<br/>- {scenario 3 description} | 1. {acceptance criteria 1}<br/>2. {acceptance criteria 2} | [Requirement Tasks](./02_requirement-tasks.md)<br/>[Design Document](./03_design-document.md)<br/>[Project Report](./07_project-report.md) | [Generate Document Skill](../../.claude/skills/generate-document/SKILL.md)<br/>[Requirement Document Specification](../../.claude/skills/generate-document/rules/requirement-document.md)<br/>[Requirement Document Template](../../.claude/skills/generate-document/templates/requirement-document.md)<br/>[Requirement Document Checklist](../../.claude/skills/generate-document/checklists/requirement-document.md) |

**User story format**: `As [role], I want [feature], so that [value]` — role clear, feature actionable, value clear.

### 4. Document Specifications (Must Include)

- One numbered set corresponds to one user story
- Anti-hallucination: content that cannot be determined from repository facts/upstream write `> Pending confirmation (reason: …)`

### 5. Acceptance Criteria

- **P0**: Core feature, cannot release without implementation
- **P1**: Important feature, recommended to implement
- **P2**: Nice-to-have, optional implementation

### 6. Feature Details

- Chaptered by feature point, each containing: feature description, boundaries and exceptions, value/motivation
- Only write "what to do", do not write implementation details

### 7. Usage Scenario Examples

- Each scenario: background, operation, result, identified with 📋🎨 and other icons

## Save Location

`docs/<feature-name>/01_requirement-document.md`

## Quality Check

> See [checklists/requirement-document.md](../checklists/requirement-document.md)
