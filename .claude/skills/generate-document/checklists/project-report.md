# Project Report Checklist

> **Related specs**: [Project Report Spec](../rules/project-report.md) | [General Document Checklist](./general-document.md)

## P0 — Must Pass

- Document header is complete
- Report scope is explicit (included / excluded / uncertain items all have explanations)
- Delivery summary is traceable (delivery goals, core results, change scale, and verification conclusions all have sources)
- Changed file list is complete (consistent with git diff or user-provided list)
- Each changed file has before/after comparison
- Pre-change content is real (from the old version, not inferred)
- Paths are real and valid
- Summary table is complete (every changed file appears with verification coverage status)
- Verification results are real (executed / not executed / failed recorded truthfully)
- Self-improvement chapter exists and is evidence-based

## P1 — Should Pass

- Change overview is clear (overall change can be understood from change domains)
- Impact assessment is complete (covers 5 impact surfaces)
- Risks and carryover items are explicit
- Impact assessment is reasonable (none/low/medium/high consistent with actual change scope)
- Key excerpts are appropriate

## P2 — Nice to Have

- Reader-layering friendly
- Change scale numbers match the list
