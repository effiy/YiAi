# General Document Checklist

> **Related specs**: [General Document Spec](../rules/general-document.md) | [Evidence and Uncertainty](../../../shared/evidence-and-uncertainty.md)

## P0 — Must Pass

- Document header structure is complete (contains all elements in general-document spec order)
- Metadata is complete (version, last updated date, maintainer)
- Version format is correct (`v{major}.{minor}`)
- Date format is correct (`YYYY-MM-DD`)
- Related docs line, Git branch line, and document timeline line all exist
- Separator `---` between header and body
- H1 is unique; heading depth does not exceed H3
- Mermaid diagrams have explanations
- Links use relative paths
- Technical assertions are traceable
- No fabricated paths or dependencies
- Gaps are explicit (unsupported paragraphs use `> To be supplemented (reason: …)`)
- Open questions are convergent (items requiring human decisions are not mixed with factual statements in the same paragraph)

## P1 — Should Pass

- Paragraphs are separated by blank lines; length is moderate (no more than 3–4 lines)
- Lists are used appropriately
- Tables are well-formatted
- Code blocks have language tags
- Related documents exist
- Headings are clearly named

## P2 — Nice to Have

- Mermaid node styles are consistent
- Icons are used uniformly
- Chapter navigation
- Important information uses blockquotes
