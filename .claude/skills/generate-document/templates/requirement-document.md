# {Feature Name}

> **Document Version**: v1.0 | **Last Updated**: {date} | **Maintainer**: {Model Name} | **Tool**: {Claude Code / Cursor}
>
> **Related Documents**: [Requirement Tasks](./02_requirement-tasks.md) | [Design Document](./03_design-document.md) | [Usage Document](./04_usage-document.md) | [CLAUDE.md](../../CLAUDE.md)
>
> **Git Branch**: {branch-name}
>
> **Doc Start Time**: {HH:mm:ss} | **Doc Last Update Time**: {HH:mm:ss}
>

[Feature Overview](#feature-overview) | [User Stories and Feature Requirements](#user-stories-and-feature-requirements) | [Acceptance Criteria](#acceptance-criteria) | [Feature Details](#feature-details)

---

## Feature Overview

{3-6 sentences describing goals, scope, and non-goals. Reference repo facts; if uncertain mark `> TBD (reason: …)`.}

**Core Values**
- 🎯 {value1}
- ⚡ {value2}
- 📖 {value3}

---

## User Stories and Feature Requirements

**Priority icons**: 🔴 P0 - must have | 🟡 P1 - should have | 🟢 P2 - nice to have

| User Story | Acceptance Criteria | Process Generated Docs | Produced Smart Docs |
|------------|---------------------|------------------------|---------------------|
| 🔴 As [role], I want [feature], so that [value]<br/><br/>**Main Operation Scenarios**:<br/>- {scenario1}<br/>- {scenario2}<br/>- {scenario3} | 1. {criteria1}<br/>2. {criteria2} | [Requirement Tasks](./02_requirement-tasks.md)<br/>[Design Document](./03_design-document.md)<br/>[Project Report](./07_project-report.md) | [Generate Document Skill](../../.claude/skills/generate-document/SKILL.md)<br/>[Requirement Document Spec](../../.claude/skills/generate-document/rules/requirement-document.md)<br/>[Requirement Document Template](../../.claude/skills/generate-document/templates/requirement-document.md)<br/>[Requirement Document Checklist](../../.claude/skills/generate-document/checklists/requirement-document.md) |

---

## Document Spec

- **One numbered set per user story**
- **Anti-hallucination**: uncertain content write `> TBD (reason: …)`

---

## Feature Details

> Only write "what to do / what not to do", not implementation details.

### {Feature Point 1 Title}

- **Description**: {user-perceivable behavior, constraints, input/output}
- **Boundaries and Exceptions**: {failure prompts, fallback strategy}
- **Value/Motivation**: {why it's needed}

---

## Acceptance Criteria

### P0 - Must Pass
- [ ] **Item 1**: {reproducible steps + expected result + failure behavior}
- [ ] **Item 2**: {cover at least 1 boundary condition}

### P1 - Should Pass
- [ ] **Item 3**: {performance/usability/accessibility}

### P2 - Nice to Have
- [ ] **Item 4**: {nice-to-have}

---

## Usage Scenario Examples

#### 📋 Scenario 1: {Scenario Title}

> **Background**: {1-2 sentences}
>
> **Operation**: {user specific operation steps}
>
> **Result**: {expected result and value}
