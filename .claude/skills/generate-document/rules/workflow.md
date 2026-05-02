---
paths:
  - "docs/*/01_requirement-document.md"
  - "docs/*/02_requirement-tasks.md"
  - "docs/*/03_design-document.md"
  - "docs/*/04_usage-document.md"
  - "docs/*/05_dynamic-checklist.md"
  - "docs/*/07_project-report.md"
---

# Feature Document 5+1 Step Workflow

> Applicable to `/generate-document <feature-name>-<description>`. Differences for `init`/`weekly`/`from-weekly` see `../SKILL.md`.
> Core principles and review gates follow `../SKILL.md`; stage state machine see `orchestration.md`.

## Step 0: Smart Planning (Optional but Recommended)

- **Trigger**: Before feature document generation, before Step 1
- **Invoke `doc-planner`**: Pass feature name and description, read historical similar cases from `docs/.memory/execution-memory.jsonl`
- **Output**: Adaptive execution plan, containing:
  - Feature characteristic fingerprint (domain / module / change type)
  - Historical similar case list and actual change levels
  - **Suggested change level** (T1/T2/T3 tendency and basis)
  - Agent invocation strategy (strengthen / trim / normal)
  - Risk warning (high-frequency problem points from historical cases)
  - Custom check items (special additions this round)
- **Processing Rules**:
  - When execution memory is empty: annotate "First execution, no historical reference", skip this step and directly enter Step 1
  - Skill may adjust planner suggestion based on actual detection results, but must record adjustment reason in orchestration logs
  - Planner suggestion is **reference input**, final change level determination is based on actual document differences in Step 1

## Step 1: Parsing + Specification Retrieval + Existing Document Detection + Change Grading

- Extract `{feature-name}`
- **Detect existing documents**: Does `docs/{feature-name}/` contain valid Markdown?
  - Does not exist: New mode
  - Already exists: Load 01-03 → Compare with user input → Identify differences → Produce **change impact table**
- **Change grading (mandatory)**:
  - Reference Step 0 `doc-planner` output "suggested change level" as initial determination basis
  - If planner suggestion conflicts with detection result, prioritize actual document differences, and record conflict reason in logs

| Level | Criteria | Handling Strategy |
|-------|----------|-------------------|
| **T1 Minor** | Typos, formatting adjustments, added examples/descriptions, wording optimization, does not change facts and boundaries | Only rewrite changed chapters/paragraphs of target document, do not trigger any downstream updates |
| **T2 Partial** | Supplement to a requirement point, interface parameter adjustment, new/modified check items, local process changes, does not touch feature boundaries | Rewrite target document changed chapters + sync update **downstream documents' corresponding entries that directly reference this chapter** (e.g. 01 requirement supplement → 02 sync corresponding entry; 03 interface parameter adjustment → 04 sync corresponding operation description) |
| **T3 Scope** | Feature boundary changes, new/deleted modules, interface signature changes, architecture pattern adjustments | Trigger full cascade refresh: 01→02/03→04/05→07 |

- **Must invoke `docs-retriever`** (In update mode, if document type is unchanged, may reuse last specification set)
- Output: Feature name, specification set, upstream list, existing document status, **change impact table (including level determination and affected chapter list)**

## Step 2: Upstream Grounding + Impact Analysis

- Read 01→02→03 in dependency order; design document simultaneously reads relevant source code
- **Must invoke `doc-impact-analyzer`** (only 02/03): First read `../../../shared/impact-analysis-contract.md`
- Impact chain written to chapter 6 of 02 / chapter 5 of 03
- Output: Fact-source mapping table, impact chain closure

## Step 3: Expert Generation

- **Must invoke `codes-builder`** (before 03 generation)
- **Must invoke `doc-architect`** (before 03 generation): 5 mandatory questions must be adopted into 03 architecture chapter
- Output: Design plan, module division, interface specifications

## Step 4: Per-Document Generation + Self-Check

### Generation Strategy

New: Complete output in chapter order according to `rules/<type>.md`.

Update strategy (execute according to change level determined in Step 1):

| File | T1 Minor | T2 Partial | T3 Scope |
|------|----------|------------|----------|
| **01** | Rewrite changed chapters, unchanged retain original | Rewrite changed chapters + 02 sync corresponding entries (only affected entries) | Full rewrite → 02 full sync → trigger 03 rebuild |
| **02** | Rewrite changed entries, unchanged retain original | Rewrite changed entries + 03 corresponding module/interface adjustment (only affected parts) | Full rewrite → trigger 03 rebuild |
| **03** | Rewrite changed chapters, unchanged retain original | Rewrite changed chapters + 04 corresponding operation update (only affected operations) | Full rewrite → trigger 04 rebuild |
| **04** | Rewrite changed paragraphs, unchanged retain original | Rewrite changed paragraphs + sync terminology and path changes | Full rebuild according to latest 03 status |
| **05** | Rewrite changed check items, unchanged retain original | Extract new/modified check items from 02/03, append under corresponding scenarios | Full re-extract from latest 02/03 |
| **07** | Append this change record | Append this change record + verification conclusion | Append this change record + verification conclusion |

**Update Principles**:
- **Default minimum impact**: When no sufficient evidence, handle as T1, must not "just to be safe" upgrade change level
- **Chapter-level retention**: Unchanged chapters must retain original text verbatim, rewriting is prohibited
- **Reference tracking**: T2 changes must explicitly annotate "Synced due to chapter X change in 01/02/03"
- **Impact analysis reuse**: For T1/T2 changes, if change scope does not exceed last round's impact analysis boundary, may reuse last round's impact analysis result, only supplement new impact points

### Three-Layer Review Gate

1. **Syntax layer**: Contains Mermaid → `doc-mermaid-expert` review and write back
2. **Quality layer**: Design document → `doc-reviewer` (P0 fixed before saving)
3. **Test layer**: `doc-markdown-tester` verify links/code/terminology

### Self-Check and Quality Statistics

- Load `checklists/<type>.md`, P0 all passed before saving; at most 1 round of self-repair
- `doc-quality-tracker` statistics P0/P1/P2

## Step 5: Save + Knowledge Curation

New: Create `docs/<feature-name>/`, 01-05, 07, version `v1.0`.
Update: Overwrite affected files; patch version `+1`, breaking changes allow major version `+1`.

`docs-builder` knowledge curation:
- New mode: Complete curation
- Update mode: **Incremental curation**, only process knowledge extraction related to this change; historically curated content is not rewritten, only append "Update trigger and cascade impact" and new pitfalls/patterns

## Step 6: Document Sync and Notification (Mandatory)

> SKILL.md principle #7. `import-docs` first, then `wework-bot`, reversing is prohibited.

### import-docs

`node .claude/skills/import-docs/scripts/import-docs.js --dir docs --exts md`
Record real result for wework-bot use. When `API_X_TOKEN` is missing, record "Sync not executed this round".

### wework-bot

Follow `../wework-bot/SKILL.md` vivid summary format. Required: `⏱️ Time` / `🪙 Session Usage` / `🤖 Model` / `🧰 Tools` / `🕒 Last Updated` / `☁️ Document Sync` (fill real result when executed). Update mode: `🎯 Conclusion` reflect "Update", `📦 Artifacts` note "Update N / Keep N".
