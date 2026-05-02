---
name: search-first
description: |
  Before making technical decisions (library selection, solution selection),
  parallel-search npm / PyPI / MCP / GitHub / Web, evaluate candidates, and
  give evidence-based recommendations. Used when design documents need to
  introduce external dependencies or make technology choices.
user_invocable: true
lifecycle: default-pipeline
---

# search-first

## Purpose

Before writing any technology selection, search first. Use real data to support decisions, avoiding recommendations of outdated or non-existent libraries from memory.

## Input

- **Requirement description**: technical problem to solve (required)
- **Constraints**: such as language/framework/license requirements (optional)
- **Search scope**: `npm` / `PyPI` / `MCP` / `GitHub` / `Web` (defaults to all parallel)

## Workflow

1. **Requirement decomposition**: extract functional keywords and constraints from description
2. **Parallel search** (launch simultaneously):
   - npm / PyPI: search package names, weekly downloads, last update
   - GitHub: search stars, open issues, last commit
   - MCP: search available MCP tools
   - Web: search latest docs, known issues, community reviews
3. **Evaluation matrix**: score each candidate

| Candidate | Function Coverage | Maintenance Activity | Community Size | License | Overall |
|-----------|-------------------|----------------------|----------------|---------|---------|
| A         | ⭐⭐⭐⭐⭐          | ⭐⭐⭐⭐               | ⭐⭐⭐           | MIT     | ⭐⭐⭐⭐  |

4. **Decision**: adopt / extend existing / combine / build in-house

## Output Format

```
Recommended solution: <solution name>
Rationale: <2-3 sentences based on search data>
Source: <URL or package@version>

Alternative: <solution name> (applicable scenario: <when to use alternative>)

Uncovered by search: <parts that cannot be verified through search, needs human confirmation>
```

## Usage Rules

- All recommendations must have verifiable sources (URL / package@version).
- When search results do not match requirements, output "no solution meeting constraints found," **do not guess**.
- If no network access, explicitly state "cannot execute search, below is reference based on training data (may be outdated)."
