---
name: code-review
description: |
  Review code examples and architecture implementations against project conventions
  (entry initialization, state management patterns, component registration/export,
  coding standards, etc.). Used when project reports or dynamic checklists contain
  code implementation validation scenarios.
user_invocable: true
lifecycle: default-pipeline
---

# code-review

## Purpose

Perform normative review on specified code files or snippets, outputting a P0/P1/P2 graded issue list.

This skill defines the review method, dimensions, and output format. For parallel expert roles or required questions, use `../../agents/code-reviewer.md`. Boundaries: `../../shared/agent-skill-boundaries.md`.

## Input

- **Review target**: file path list or code snippet (required)
- **Context**: related design document chapter or feature description (optional)
- **Focus area**: such as `architecture consistency` / `security` / `performance` (optional, defaults to full review)

## Review Dimensions

### Project-Specific (apply per repository status)

- **Entry initialization pattern**: does the view entry follow the project's existing initialization method?
- **State management pattern**: does the Store/state layer follow the project's existing organization?
- **Shared component registration/export**: are shared components managed centrally per project convention and correctly referenceable?
- **Code structure**: does it conform to `../generate-document/rules/code-structure.md`?
- **Coding standards**: does it conform to `../generate-document/rules/coding-standard.md` (naming, comments, formatting)?

### Universal Quality

- **Readability**: are function/variable names clear, are necessary comments present?
- **Boundary handling**: are null values and exception paths handled?
- **Security**: are there XSS / CSRF / sensitive information leak risks?
- **Performance**: are there obvious unnecessary renders / memory leak risks?

## Output Format

```
Review Results:
P0 (must fix):
  - file:line — <issue description> — <fix suggestion>

P1 (suggested fix):
  - file:line — <issue description>

P2 (optional optimization):
  - file:line — <issue description>

No-issue items: <explicitly state if a dimension has no issues>
```

## Usage Rules

- Read `../generate-document/rules/code-structure.md` and `../generate-document/rules/coding-standard.md` as judgment basis.
- Only review **actually read code**; do not infer unseen file content.
- When files cannot be accessed, output "Cannot read file <path>, skipping."
