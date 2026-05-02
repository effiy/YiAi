---
paths:
  - "docs/*/07_project-report.md"
  - "docs/**/07_project-report.md"
generate_mode: rules-only
template: disabled
---

# Project Report Specification

> **Template disabled**. All content must come from real sources (user goals, upstream docs, git diff, source code, verification logs); if no source write "TBD (reason: ...)", do not fabricate.
> Upstream: 01-05, 06 (if exists).

## Generation Prerequisites (P0)

If any of the following is not met, **abort generation**:

1. Can access changed file list (git diff / git status / user provided)
2. Pre-change content is readable (new files may have none)
3. At least one associable upstream document (prefer `03_design-document.md`)
4. Can distinguish this scope change from workspace-unrelated changes

## Document Structure

### 1. Header

Standard header + navigation anchor links (Delivery Summary | Report Scope | Change Overview | Impact Assessment | Verification Results | Risks | Changed Files | Change Comparison | Change Summary).

### 2. Delivery Summary

3-5 bullet points: goal, core results, change scale, verification conclusion, current status. All must have sources.

### 3. Report Scope

| Scope Item | Content | Source |
Included / Excluded / Uncertain items (if none write "none")

### 4. Change Overview

| Change Domain | Before | After | Value/Impact | Source |

Before/after must come from diff or old files, do not infer.

### 5. Impact Assessment

| Impact Surface | Level | Impact Description | Basis | Disposal Suggestion |

Impact surfaces: user experience / feature behavior / data interface / build deploy / doc collaboration. Level: high=affects public interface/Store/routes/persistence/build/deploy; medium=single module/main flow/doc contract; low=local UI/style/copy; none=confirmed not involved.

### 6. Verification Results

| Verification Item | Command/Method | Result | Evidence | Notes |

Not executed write "not executed"+reason; failure keeps summary and do not weaken; reference dynamic checklist corresponding items.

### 7. Risks and Legacy Items

| Type | Description | Severity | Follow-up Action | Source |

Types: risk/legacy/TBD. No risks write: 「No clear legacy risks identified (basis: diff/verification logs/upstream doc scope)」.

### 8. Changed File List (Mandatory, complete)

| # | File Path | Change Type | Change Domain | Description |

Paths must come from git diff / git status / user confirmed list, prohibit "guessing" from design document.

### 9. Before/After Comparison (Mandatory, one section per file)

File path → change type → before → after → one-sentence description.
- "Before" must come from real old version
- Over 100 lines: extract key fragments and note "truncated"
- New files: "before" write `(new file, no before content)`
- Deleted: "after" write `(deleted, no after content)`

### 10. Change Summary Table (Mandatory)

| File Path | Change Type | Change Domain | Impact Assessment | Key Changes | Verification Coverage |

Impact assessment criteria same as section 5.

### 11. Skills/Agents/Rules Self-Improvement (Evidence-driven, mandatory, at document end)

**Only summarize this round's real facts**; each improvement must have traceable evidence; suggestions must land on concrete executable actions (give path and minimum change point).

Three sub-sections: did poorly (phenomenon+evidence+impact) → executable improvement suggestions (category+suggested path+change point+expected benefit+verification method) → un-evidenced hypotheses (class C).

## Save Location

`docs/<feature-name>/07_project-report.md`

## Quality Check

> See [checklists/project-report.md](../checklists/project-report.md)
