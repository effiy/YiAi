# Weekly Report Checklist

> **Related specs**: [Weekly Report Spec](../rules/weekly-report.md) | [General Document Checklist](./general-document.md)

## P0 — Must Pass

- Document header is complete (version, date, maintainer, coverage period, associated feature directories); when no active feature directories, write "no active feature directories this week"
- KPI data source is automated (`collect-weekly-kpi.js --with-logs` executed and output adopted)
- KPI master table coverage (each feature directory with KPI data occupies one row; do not fabricate directories when no data)
- KPI quantification and evidence (five dimensions have concrete values and paths)
- Dimension synthesis is grounded (✅/🟡/❌ and rationale consistent with 06/05 and other sources)
- This-week retrospective is non-empty (contains progress/highlights and problem root causes)
- Pipeline panoramic diagram is correct (KPI → retrospective root cause → future planning, no OKR node)
- Future planning master table is actionable (each item has type label, KPI metric, verification method, and evidence)
- First future-planning item corresponds to the weakest KPI
- Improvement items contain a "reference standard" field that is industry-common practice rather than theoretical book titles
- Workflow standardization four questions have been reviewed (write "none" if absent; skipping prohibited)
- Prohibit quadrant diagrams, matrix diagrams, and other visual priority expressions
- Anti-hallucination (no fabricated data, cases, or Class-D statements)

## P1 — Should Pass

- Git statistics match script output
- Pipeline causality is accurate (weak KPI links to root cause and first planning item)
- Future planning priority is reasonable (first item corresponds to weakest KPI)
- Coverage period is correct (natural week start and end)
- Step 6 executed (import-docs first, then wework-bot)
- Execution memory has been written (after feature document delivery)
- self-improve triggered and output improvement proposals (weekly command)
- doc-mermaid-expert has been called
- Executed to completion in one shot (no interruption for non-blocking reasons, no "to be supplemented" placeholder left unaddressed, no split into multiple rounds)

## P2 — Nice to Have

- Cross-week comparison
- High executability of improvement suggestions
