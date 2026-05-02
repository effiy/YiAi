---
paths:
  - "docs/**/05_dynamic-checklist.md"
  - "docs/**/*checklist*.md"
generate_mode: rules-only
template: disabled
---

# Dynamic Checklist Specification

> **Template disabled**. Every scenario, check item, and verification tool must be traceable to an upstream document or code.
> Upstream: `02_requirement-tasks.md`, `03_design-document.md`; downstream: project report.

## Generation Prerequisites (P0)

If any of the following is not met, **abort generation**:

1. `02_requirement-tasks.md` contains "Main Operation Scenarios" (at least 1 complete scenario)
2. `03_design-document.md` contains "Main Operation Scenario Implementation" (each scenario has a corresponding implementation)
3. Key code paths referenced in the design document **actually exist** in the repository

## Fact-Source Mapping (Mandatory)

| Fact Type | Source Constraint |
|-----------|-------------------|
| Scenario name / preconditions / steps / expected results | Corresponding chapter in requirement tasks |
| Related modules / code paths / verification points | Design document or actual files |
| Verification tools / skills | `find-skills` return; if not found mark "recommend manual review" |
| Priority | Per this spec's "Priority Determination" |

## Document Structure

### 1. Header

Standard header + navigation anchors (General Checks | Scenario Verification | Feature Implementation | Code Quality | Testing | Check Summary).

### 2. General Checks (Mandatory, fixed four rows)

| Check Item | Priority | Status | Notes |
Title format correct (P0) | Linked document links valid (P0) | Related files created/updated (P0) | Project buildable (P0)

### 3. Main Operation Scenario Verification (Mandatory, dynamically generated)

**Each** requirement task scenario generates one section (count = requirement task scenario count, do not add or remove).

Each section structure: scenario name → linked requirement task anchor + linked design document anchor → verification tool recommendation (`find-skills` mapping) → preconditions verification table → operation steps verification table → expected results verification table → verification focus points table.

**Constraint**: check items must be verifiable restatements of upstream original text; adding conditions not in the original is prohibited; verification methods must be specific; when upstream is missing write `> TBD (reason: not found in <upstream>#<chapter>)`.

### 4. Feature Implementation Checks (As needed)

Only included when the design document explicitly lists feature points. Sub-chapters: core (P0) → boundaries (P1) → error handling (P1/P2). Each must correspond to a specific paragraph in the design document.

### 5. Code Quality Checks (Mandatory)

| Check Item | Priority | Status | Verification Method |
Style compliance (P1) | Naming clarity (P1) | Performance (P2) | Security risks (P0)

### 6. Testing Checks (Mandatory, fixed four rows)

| Check Item | Priority | Status | Verification Method |
Unit coverage core (P1) | E2E coverage main scenarios (P0) | P0 tests all passed (P0) | Test report complete (P1)

### 7. Check Summary (Mandatory)

Three sub-sections (initial value 0): overall progress (category/total/completed/pass rate) → pending items (checkbox) → conclusion (initial `⏳ check not started`).

## Priority Determination

- **P0**: main flow availability, data consistency, security, build
- **P1**: experience/maintainability (does not block main flow)
- **P2**: optional optimizations

## Save Location

`docs/<feature-name>/05_dynamic-checklist.md`

## Quality Check

> See [checklists/dynamic-checklist.md](../checklists/dynamic-checklist.md)
