---
paths:
  - "docs/**/*.md"
---

# General Document Specification

## Document Header (Strict)

```markdown
# {Document Title}

> **Document Version**: v{version} | **Last Updated**: {YYYY-MM-DD} | **Maintainer**: {Model Name} | **Tool**: {Claude Code / Cursor}
>
> **Related Documents**: [Related Doc 1](../dir/{filename}.md) | [Related Doc 2](../dir/{filename}.md)
>
> **Git Branch**: {branch-name}
>
> **Doc Start Time**: {HH:mm:ss} | **Doc Last Update Time**: {HH:mm:ss}
>

[Chapter 1](#chapter1) | [Chapter 2](#chapter2) | [Chapter 3](#chapter3)

---
```

Header parts (in order): H1 title → blank line → metadata line 1 (version/date/maintainer) → blank line → related docs line → blank line → Git branch line → blank line → doc time line → blank line → chapter navigation (recommended) → separator `---`.

**Metadata spec**:
- Version: `v{major}.{minor}`, new docs start at `v1.0`
- Last updated: `YYYY-MM-DD`
- Maintainer: model name (e.g. `Claude Sonnet 4.6`)
- Git branch: branch name when generated
- Doc time: `HH:mm:ss` (24h); if start time unavailable write "unknown (not recorded)"

## Heading Levels

- **H1** (`#`): document main title, unique
- **H2** (`##`): major chapters
- **H3** (`###`): sub-chapters
- **H4 and below**: prohibited

## Mermaid Chart Specification

### Chart Type Selection

- Architecture/function decomposition/module division: `graph TB`
- Component relationships/flow steps/dependencies: `graph LR`
- Flow with decisions: `flowchart TD`
- Sequence interaction/data flow/call chain: `sequenceDiagram`

### Node Style Colors

- Positive/new/core: `fill:#ccffcc`
- Negative/issue: `fill:#ffcccc`
- Keep/neutral/spec: `fill:#e1f5ff`

### Chinese and Special Character Nodes (Mandatory)

- When node text contains Chinese, spaces, parentheses, colons or other special characters, must wrap in **double quotes**
- Correct: `A["User Login"] --> B["Validation Failed (wrong password)"]`
- Incorrect: `A[User Login] --> B[Validation Failed (wrong password)]`
- Prohibit using full-width parentheses `（）`, full-width colon `：` and other unescaped characters in node text

Each chart must have explanatory text below it.

## Formatting

- Paragraphs no more than 3-4 lines, blank line between paragraphs, one central idea per paragraph
- Parallel items use unordered lists (`-`), steps/flows use ordered lists (`1.`)
- Comparisons use tables, code examples use code blocks with language annotation
- Key terms use **bold**, filenames/paths/variables use `inline code`
- Document links use relative paths uniformly

## Quality Check

> See [checklists/general-document.md](../checklists/general-document.md)
