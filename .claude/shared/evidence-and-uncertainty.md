# Evidence, Uncertainty, and Anti-Hallucination (Shared Standard)

> This file is the shared interpretation layer for `generate-document` and `implement-code`, constraining: **any statement written to `docs/` or influencing implementation decisions must be verifiable or explicitly labeled as unknown**; smooth narrative must not mask missing evidence.

## 1. Truth Levels

| Level | Meaning | How to Write in Documents |
|-------|---------|---------------------------|
| A Verified | Verifiable in this repository via Read / Grep / Glob or already-read `docs/` anchor | State directly, give `path` or `document§section` |
| B Derivable | Derived one step from A in this document via an explicit rule | Write "from … it follows", and chain back to A |
| C Unverified | User verbal statement, un-crawled external web, or unexecuted tool | Must use `> To be supplemented (reason: …)` or `awaiting reader confirmation` |
| D Prohibited | Unsupported by A/B and not falling under C | **Must not appear** (treated as hallucination) |

**Rule**: Jumping from A to a conclusion while skipping a stated rule in B makes that conclusion D.

## 2. Prohibited Statements (Class D, strictly forbidden)

- Writing "the project already has module X / API Y" without executing Grep / Glob / Read.
- Writing specific file paths, export names, version numbers, or environment variable names that do not exist in the repository or were not read.
- Fabricating dependency relationships, test files, or configuration items to pad out "impact analysis / design chapters".
- Writing capability names returned by `find-skills` / `find-agents` as already-selected skills or already-invoked agent names when they were **not** returned (names must match return values or be labeled "no match").

## 3. Admissibility (Practical Standard for Humans)

**Adoption rate** depends on whether the reader can quickly **verify** and **complete**, not on length. Must satisfy all three:

1. **Verifiable**: Technical sentences have sources (`path` or `docs/...md` heading/anchor); diagram nodes map to real modules or are labeled "planned".
2. **Completable**: All Class-C items are listed centrally (open questions, missing inputs, materials suggested for the user to provide).
3. **Actionable**: If "next step" is an action, it must bind to a **verification method** (command, file to open, or checklist item number to check); do not write vacuous slogans like "optimize performance" or "improve experience".

## 4. Integration with `implement-code`

- Scenarios in `02_requirement-tasks` and checklist items in `05_dynamic-checklist` should be traceably mapped; after `generate-document` full-set output, the implementer should be able to produce a **scenario–checklist coverage table** at stage 0 (see `implement-code/rules/orchestration.md`).
- "Follow-up recommendations" and "self-improvement" in `06_process-summary` must comply with **§1–§3** of this file; structure for §9 see `implement-code/rules/process-summary.md`.

## 5. Revision Principle

- When historical documents are found to contain Class-D statements: **do not** "conveniently fix" domain conclusions without evidence; convert to Class-C and point out the need for human confirmation or code verification.

---

**Source-of-truth priority**: `skills/.../SKILL.md` > `shared/evidence-and-uncertainty.md` and `rules/*.md` referenced by this file > other explanatory READMEs.
