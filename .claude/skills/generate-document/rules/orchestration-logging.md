---
paths:
  - "docs/weekly/*/logs.md"
  - "docs/weekly/*/key-notes.md"
---

# Orchestration Session Logs and Key Nodes

> See `orchestration.md` for stage state machine and gates; see `../SKILL.md` for core principles.

---

## 1. Interaction Logs (Mandatory)

Every time this skill is executed, after each completed round of interaction, must append to `docs/weekly/<YYYY-MM-DD>~<YYYY-MM-DD>/logs.md`:

| Interaction Category | `--kind` Value | Example |
|----------------------|----------------|---------|
| Skills under `.claude/skills/` | `skill` | `import-docs`, `wework-bot` |
| Agents under `.claude/agents/` | `agent` | `docs-retriever`, `doc-impact-analyzer` |
| MCP tools | `mcp` | Record tool identifier and call highlights |
| Contracts under `.claude/shared/` | `shared` | `impact-analysis-contract.md` |
| Memory files under `.claude/` | `memory` | Project memory, user preferences |
| Other | `other` | git commands, external scripts |

### 1.1 Record Structure

Each entry contains: **Operation Scenario** (`--scenario`), **Dialogue and Interaction Summary** (`--text` or stdin)

### 1.2 Evaluation Annotation (Optional but Recommended)

| Parameter | Description | Mandatory Level |
|-----------|-------------|-----------------|
| `--case good\|bad\|neutral` | This round's interaction quality judgment | Recommended; bad case recommended with `--lesson` |
| `--tags "<tag1,tag2>"` | Categorization tags | Optional |
| `--lesson "<one-sentence follow-up improvement>"` | Improvement suggestion for bad case | Recommended for bad case |

### 1.3 Command

```bash
node scripts/log-orchestration.js --skill generate-document \
  --kind <skill|agent|mcp|memory|shared|other> [--name <identifier>] \
  [--scenario "<operation scenario>"] \
  [--case <good|bad|neutral>] [--tags "<tag1,tag2>"] [--lesson "<follow-up improvement>"] \
  [--text "<one-line summary>"]
```

### 1.4 Blocking Fallback

Even if blocked midway, logs for interactions that have already occurred must still be completed before ending; silent omission is prohibited.

---

## 2. Key Node Records (Recommended)

Stage switches, gate conclusions, external notifications, and other milestones are recommended to be appended to `docs/weekly/<YYYY-MM-DD>~<YYYY-MM-DD>/key-notes.md`.

### 2.1 Command

```bash
node scripts/log-key-node.js --title "<node title>" \
  [--category <category, default general>] \
  [--skill <associated skill name>] \
  [--text "<description>"]
```

Common `--category`: `stage` (stage switch), `gate` (gate conclusion), `notify` (external notification).

### 2.2 Recommended Recording Timing

| Timing | `--category` | `--title` Example |
|--------|--------------|-------------------|
| Stage switch | `stage` | "Stage 3 completed: doc-architect adopted" |
| Gate conclusion | `gate` | "doc-impact-analyzer gate passed" |
| Step 6 completed | `notify` | "wework-bot notification sent successfully" |
| Blocking occurs | `gate` | "Stage 2 blocked: impact chain not closed" |

---

## 3. Relationship with Weekly Report

- `logs.md` → Orchestration logs: root-cause evidence source for weekly report "This Week's Review"
- `key-notes.md` → Key nodes: at-a-glance source for weekly report "Progress and Highlights"

---

## 4. Script Paths

| Script | Actual Path |
|--------|-------------|
| `log-orchestration.js` | `skills/generate-document/scripts/log-orchestration.js` |
| `log-key-node.js` | `skills/generate-document/scripts/log-key-node.js` |
