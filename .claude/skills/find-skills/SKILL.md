---
name: find-skills
description: |
  Discover and recommend available skills in .claude/skills/ based on task
  description and keywords. Used when finding suitable skill combinations for
  a given task.
user_invocable: true
lifecycle: default-pipeline
---

# find-skills

## Purpose

Discover available skills in the current project's `.claude/skills/` directory, and recommend optimal combinations by task type.

Directory conventions and source of truth: `../../README.md`; for Skill vs Agent boundaries, see `../../shared/agent-skill-boundaries.md`.

## Input

- **Task description**: ≤ 100 word summary (required)
- **Keyword list**: such as `["E2E", "security review", "document generation"]` (optional, helps precise matching)

## Workflow

1. List all subdirectories under `.claude/skills/`
2. Read each subdirectory's `SKILL.md` frontmatter `description` field
3. Perform semantic matching between task description, keywords, and each skill's description, score and sort
4. Return recommendation results

## Output Format

```
Recommended skills:
- <skill name>: <applicability reason> (confidence: high / medium / low)

Alternative skills:
- <skill name>: <applicability reason>

No match found:
- Task keyword "<X>" has no corresponding skill in existing skills, suggest manual review
```

## Usage Rules

- **No fabrication**: only return skill directory names that truly exist under `.claude/skills/`; if no match is found, output "no suitable skill found."
- **Name consistency**: returned skill names must exactly match directory names, no case or alias changes.
- **Confidence standards**:
  - High: description and task highly overlap (≥ 2 keyword hits)
  - Medium: description and task partially overlap (1 keyword hit)
  - Low: no direct keyword hit, but domain-related
