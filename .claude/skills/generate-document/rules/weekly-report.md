---
paths:
  - "docs/weekly/**/*.md"
generate_mode: rules-only
template: disabled
---

# Weekly Report Specification

> **Template disabled**. Content must come from real sources (full docs set, git logs, agent memory); if no source write "TBD".

## Dynamic Context Reading (must execute before generation)

1. Run `scripts/collect-weekly-kpi.js --with-logs` (`skills/generate-document/scripts/`)
2. Read project base files: CLAUDE.md / README.md / architecture.md / FAQ.md / auth.md / security.md
3. Supplementary verification: features not covered by scripts, manually read 01-07

## Document Structure

> Format principle: for managers, "big tables + Mermaid charts", about 3 big tables + 2~3 Mermaid.

### 1. Header

Version info + coverage period (natural week Monday-Sunday) + related feature directories

**Related feature directory format**:
- When active feature directories exist: list `docs/<feature-name>/` directory names (links not mandatory, prohibit links to non-existent paths)
- When no active feature directories: write `> No active feature directories this week`, prohibit fabricating directories or generating dead links

### 2. KPI Quantification Summary Table

Per feature row: delivery completion rate / P0 pass rate / anti-hallucination rate / fix rounds / rule coverage / comprehensive dimension (✅/🟡/❌ + basis)

Determination: delivery≥80%✅ | P0≥90%✅ | rounds≤2✅

### 3. This Week Retrospective

Progress highlights (1~3 verifiable facts) → root cause of issues (phenomenon → inference → evidence path) → comparison with last week (optional)

### 4. KPI→Retrospective→Planning Linkage Panorama (Mermaid flowchart)

KPI not met → root cause analysis → follow-up planning (causal chain)

**Syntax constraints**:
- Chinese nodes, nodes with spaces or special characters must be wrapped in double quotes, e.g. `A["KPI not met"]`
- Prohibit using full-width parentheses `（）`, full-width colon `：` and other unescaped characters in node text

### 5. Follow-up Planning and Improvements

**Principle**: demand-oriented, reference industry standards but do not apply complex methodologies. Each improvement must answer three questions: what problem does it solve? how to verify effectiveness? what happens if not done?

#### 5.1 Improvement Priority Summary Table

Merge follow-up planning + system self-improvement + project self-improvement. Each record contains:

| Field | Description |
|-------|-------------|
| Type | Planning / System / Project |
| Problem Source | Which weak KPI or root cause this week does it correspond to |
| Improvement Description | Specific, executable one-sentence description |
| Reference Standard | Industry common practice for similar problems (e.g. code review, automated testing, config-as-code), do not write book names or theories |
| Verification Method | Quantifiable acceptance criteria |
| Time Dimension | Next week / This month / Quarter |
| Professional Depth | Technical architecture / Process efficiency / Quality assurance / Team collaboration |

**Sorting rules**:
1. First item must correspond to the weakest KPI this week
2. Same priority: "closer time dimension first"
3. Prohibit using quadrant charts, matrix charts, or other visualizations to express priority

#### 5.2 Workflow Standardization Review

Mandatory questions every week (skip if none, prohibit fabrication):

1. **Repetitive labor identification**: Were there more than 2 manual repetitive operations this week? Can they be scripted or templated?
2. **Decision criteria missing**: Are there fuzzy decision points relying on personal experience? Can they be沉淀 as checklist or rules?
3. **Information silos**: Do multiple steps rely on oral transmission or temporary docs? Can they be unified into a single source?
4. **Feedback loop**: Do problems found this week have a clear follow-up owner and acceptance node?

#### 5.3 System Architecture Evolution Thinking

Only fill when there is architecture-related delivery this week:

- What is the current architecture bottleneck? (performance / maintainability / scalability / security)
- Where is the next natural evolution node?
- What are the risks and rollback plans for evolution?

### 6. AI Linkage Quality Statistics Table (Optional)

## Coverage Period

Monday to Sunday, filename `YYYY-MM-DD~YYYY-MM-DD`.
`/generate-document weekly` uses current natural week; specifying a date auto-expands to that natural week.

## Execute to Completion (Mandatory)

Weekly report generation must complete in a single round; must not interrupt or downgrade to "will supplement later" for any non-blocking reason.

- **Missing info handling**: write "TBD", "no data this week", "not recorded", do not stop waiting for user supplement
- **Blocking threshold**: only when hitting H1-H4 blocking conditions (see `orchestration.md §4`) may interrupt; after interruption must still execute step 6 (import-docs → wework-bot)
- **Prohibited behaviors**: prohibit saying "please provide XX data before continuing", prohibit splitting weekly report into multiple rounds, prohibit skipping entire weekly report because one feature directory is missing

## Anti-Hallucination

KPI values inferred from actuals / retrospective root causes must have traceable evidence / planning must correspond to verifiable KPI / no feature directories must be stated truthfully

## Mermaid Review (Mandatory)

Before finalizing, `doc-mermaid-expert` reviews and writes back.

## Quality Check

> See [checklists/weekly-report.md](../checklists/weekly-report.md)
