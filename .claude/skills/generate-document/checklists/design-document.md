# Design Document Checklist

> **Related specs**: [Design Document Spec](../rules/design-document.md) | [General Document Checklist](./general-document.md)

## P0 — Must Pass

- Design overview and architecture design chapters exist
- Overall architecture diagram exists (Mermaid graph TB/LR)
- Impact analysis chapter exists, containing search-term and change-point list, impact chain, dependency closure summary, and uncovered risks
- Impact chain is based on actual search (paths and line numbers must not be estimated)
- Dependency relationships are closed
- Change scope summary exists
- Fix/change content, implementation details, and main operation scenario implementation chapters exist (for full-set generation)

## P1 — Should Pass

- Impact chain dimensions and disposition methods are fully labeled
- Module division table and core flow diagram exist
- Mermaid diagrams have explanations
- Before/after comparison is clear
- Key code explanations exist
- Scenario implementations contain key code paths and verification points

## P2 — Nice to Have

- Design principles list exists
- Mermaid node styles are consistent
- Test considerations are complete
