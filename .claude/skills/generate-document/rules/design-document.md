---
paths:
  - "docs/*/03_design-document.md"
generate_mode: rules-only
template: disabled
---

# Design Document Specification

> **Template disabled**. Chapter order, naming, and charts must strictly come from this spec; modules/paths/interfaces/scenarios must be traceable upstream or to code, if no source write "TBD (reason: source not found)".
> Upstream: requirement tasks (02); downstream: usage document.

## Document Structure

### 1. Header

Standard header + navigation anchors (Design Overview | Architecture Design | Changes | Implementation Details | Impact Analysis).

### 2. Design Overview

100-200 words + 3 design principles (🎯⚡🔧)

### 3. Architecture Design (must contain Mermaid)

Overall architecture `graph TB` + explanation → module division table (name|responsibility|location) → core flow `flowchart TD` + explanation

### 4. Fixes/Changes (Mandatory)

For brand new features change title to "Changes". Problem analysis → solution (idea + file list + selection rationale) → before/after comparison

### 5. Impact Analysis (Mandatory)

> **Mandatory**: per `../../../shared/impact-analysis-contract.md` full-project impact chain closure.

Four sub-tables same as requirement tasks (search terms/impact chain/closure summary/uncovered risks) + change scope summary. Design document level goes deeper into functions/components/events/Store/routes/CSS/config.

> Unmatched items mark "reference not found", do not omit.

### 6. Implementation Details (Mandatory)

Technical points (what + how + why) → key code (50-100 lines + inline comments) → dependencies → testing considerations

### 7. Main Operation Scenario Implementation (Mandatory)

Each requirement task scenario: linked 02 scenario → implementation overview → modules and responsibilities → key code paths → verification points

### 8. Data Structure Design

Data flow diagram `sequenceDiagram` + explanation

## Save Location

`docs/<feature-name>/03_design-document.md`

## Quality Check

> See [checklists/design-document.md](../checklists/design-document.md)
