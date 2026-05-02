# Requirement Tasks Checklist

> **Related specs**: [Requirement Tasks Spec](../rules/requirement-tasks.md) | [General Document Checklist](./general-document.md)

## P0 — Must Pass

- User story table exists and is complete (4 columns)
- Priority icons are used (🔴🟡🟢)
- Main operation scenarios: at least 2 P0 user stories, at least 1 P1
- Feature decomposition diagram, user flow diagram, and feature flow diagram all exist
- Impact analysis chapter exists, containing four sub-tables: search-term and change-point list, impact chain, dependency closure summary, uncovered risks
- Impact chain is based on actual search (paths and line numbers come from real search, not estimation)
- Dependency relationships are closed
- Change scope summary exists

## P1 — Should Pass

- Complete sequence diagram exists
- Feature details, acceptance criteria (graded by P0/P1/P2 and testable), and usage scenarios chapters exist
- Usage scenario format is standard
- Operation scenarios contain preconditions, operation steps, expected results, and verification focus points

## P2 — Nice to Have

- Design document association is explicit
