---
paths:
  - "docs/*/02_requirement-tasks.md"
---

# Requirement Tasks Document Specification

> Upstream: Requirement Document (01); Downstream: Design Document.
> Core responsibility: Refine requirements into scenarios and breakdowns, carry impact analysis conclusions.

## Document Structure

### 1. Header

Standard header + navigation anchors (Feature Overview | Feature Analysis | Feature Details | Acceptance Criteria | Usage Scenario Examples).

### 2. Feature Overview

100-200 words + 3 core values (🎯⚡📖)

### 3. Feature Analysis (Must Include Mermaid)

4 chart types, each with explanatory text below:
- Feature decomposition diagram `graph TB`
- User flow diagram `flowchart TD`
- Feature flow diagram `flowchart TD`
- Sequence diagram `sequenceDiagram`

Node colors: core `#ccffcc`, neutral `#e1f5ff`

### 4. User Story Table (Must Extract from 01)

Fully extract, keep priority icons (🔴🟡🟢). **Must include main operation scenario descriptions**.

### 5. Main Operation Scenario Definitions (Must Include)

Format: Scenario name → Scenario description → Pre-conditions → Operation steps → Expected result → Verification focus points → Related design document chapters.

- P0 user story at least 2 scenarios, P1 at least 1
- Scenarios must be specific, actionable, verifiable

### 6. Impact Analysis (Must Include)

> **Mandatory**: Follow `../../../shared/impact-analysis-contract.md` for full-project impact chain closure.

Must contain four sub-tables:
1. Search terms and change point list
2. Change point impact chain
3. Dependency closure summary
4. Uncovered risks

End with change scope summary: directly modify N / verify compatibility N / trace transitive N / need manual review N.

> Unmatched search terms annotate "No reference found", must not omit this row.

### 7. Feature Details

Chaptered by feature point: feature description, value, pain point, benefit. Complex features may add Mermaid.

### 8. Acceptance Criteria

P0 (core / cannot release without) / P1 (important / recommended) / P2 (nice-to-have)

### 9. Usage Scenario Examples

Each scenario: background, operation, result, 📋🎨 identifiers.

## Save Location

`docs/<feature-name>/02_requirement-tasks.md`

## Quality Check

> See [checklists/requirement-tasks.md](../checklists/requirement-tasks.md)
