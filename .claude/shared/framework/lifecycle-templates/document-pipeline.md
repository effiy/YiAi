---
paths:
  - "shared/framework/lifecycle-templates/document-pipeline.md"
---

# Lifecycle Template: Document Pipeline

**Inherits**: `default-pipeline`

This template extends the default pipeline with rules specific to document generation skills (e.g., `generate-document`). Skills that use this template declare `lifecycle: document-pipeline` in their frontmatter.

---

## Delta Rules (Beyond Default Pipeline)

### 1. No Code Modification

The skill MUST NOT modify any source code files. It generates and updates documentation only. Any discovered code issues are reported as P1/P2 findings, not fixed.

### 2. Template vs. Specification-Driven

| Document Type | Driven By | Notes |
|---------------|-----------|-------|
| Requirement Document (`01_`) | Template + rules | Use skeleton template, then apply rule constraints. |
| Requirement Tasks (`02_`) | Template + rules | Same as above. |
| Design Document (`03_`) | Rules only | **No template allowed.** All content must trace to upstream docs or code. |
| Usage Document (`04_`) | Rules only | Same as above. |
| Dynamic Checklist (`05_`) | Rules only | **No template allowed.** Must contain executable P0 checklist items. |
| Process Summary (`06_`) | — | Written only by `implement-code`, not this skill. |
| Project Report (`07_`) | Rules + real data | Must include actual change metrics, not estimates. |

When a fact cannot be traced to a source, write:

```markdown
> Pending confirmation (reason: ...)
```

Hallucination is prohibited. Fictional sources are prohibited.

### 3. Three-Layer Review Gate

Stage 4 (Quality Assurance) must execute these reviews in order:

1. **Syntax Layer** (`doc-mermaid-expert`): Validate and repair all Mermaid diagram syntax.
2. **Quality Layer** (`doc-reviewer`): Check structural integrity, spec compliance, readability, and cross-document consistency.
3. **Test Layer** (`doc-markdown-tester`): Validate markdown structure, links, examples, and terminology consistency.

No stage may be skipped. `doc-quality-tracker` runs in parallel with these three to collect P0/P1/P2 statistics.

### 4. Cascade Refresh Rules

When updating existing documents, apply the minimum effective scope:

- **T1 (Micro change)**: Update only the target document's changed sections. Do NOT re-run impact analysis or architecture stages.
- **T2 (Local change)**: Update target document + synchronize directly affected downstream entries. Run partial impact analysis.
- **T3 (Scope change)**: Full cascade refresh of all documents 01–05, 07.

Never rewrite the entire document set "just to be safe."

### 5. Execution Memory & Self-Improvement

After Stage 5 (Curation), write the execution record:

```bash
node .claude/skills/generate-document/scripts/execution-memory.js write /tmp/session-<feature>.json
```

For `weekly` command runs, automatically trigger the self-improve engine after notification:

```bash
node .claude/skills/generate-document/scripts/self-improve.js \
  --since <week-start> \
  --output docs/weekly/<week-range>/self-improve-proposal.md
```

### 6. Document Postscript

Every generated document must append three sections at the end, in this order:

1. **Postscript: Future Planning & Improvements**
2. **Workflow Standardization Review** — mandatory four-question retrospective on the process used to produce this document. Format and extraction rules are defined in `skills/self-improving/rules/collection-contract.md` §3.
3. **System Architecture Evolution Thinking** — mandatory architecture reflection for the feature covered by this document. Format and extraction rules are defined in `skills/self-improving/rules/collection-contract.md` §4.

These sections are consumed by the `self-improving` skill for weekly aggregation.
