# Agent Output Contract (Machine-Validatable Appendix)

This file provides a **machine-validatable** output appendix convention for `generate-document` / `implement-code` when invoking expert agents. It turns soft requirements like "required answers coverage" and "key fields present" into enforceable gates.

## 1. Scope

- `agents/docs-retriever.md`
- `agents/doc-impact-analyzer.md`
- `agents/doc-architect.md`
- `agents/code-reviewer.md`
- `agents/doc-mermaid-expert.md`
- `agents/doc-quality-tracker.md`
- `agents/docs-builder.md`
- `agents/doc-generate-reporter.md`
- `agents/code-impl-reporter.md`

Other agents may opt into this contract by extending this file.

> **Note:** `doc-quality-tracker`, `docs-builder`, and `doc-generate-reporter` have no specific required-question sets; their `required_answers` field may be an empty array `[]`, but the `artifacts` field must still indicate key artifact existence.

## 2. Mandatory JSON Appendix Block

Every agent output **must** append a JSON fenced code block at the end, shaped like:

```json
{
  "agent": "docs-retriever",
  "contract_version": "1.0",
  "task": {
    "skill": "generate-document",
    "stage": "stage-1",
    "doc_type": "requirement-document",
    "feature": "Foo-item-filter"
  },
  "required_answers": [
    { "id": "Q1", "answered": true, "evidence": ["skills/generate-document/rules/requirement-document.md"] }
  ],
  "artifacts": {
    "required_specs": ["skills/generate-document/rules/general-document.md"],
    "optional_specs": []
  },
  "warnings": [],
  "notes": "One-line summary"
}
```

### Field Requirements

- **agent**: Must equal the agent's `name` (e.g. `docs-retriever`).
- **contract_version**: Currently fixed at `"1.0"`.
- **task.skill**: `generate-document` or `implement-code`.
- **task.stage**: For `generate-document`, use `stage-1` through `stage-6`; for `implement-code`, use the stage identifiers defined in its rules.
- **task.doc_type**: The document type targeted by this invocation; use `"N/A"` when not applicable.
- **required_answers**: Must cover the full set of "required answers" defined by the agent; each item's `answered` must be `true`, otherwise the contract is considered unfulfilled.
- **artifacts**: Structure the agent's key artifacts (e.g. spec lists, impact-analysis tables, architecture diagrams) as "existence" indicators.
- **warnings**: Non-blocking risk items that should be explicitly surfaced to the main flow.
- **notes**: One-line summary for logging and notification referencing.

## 3. Gate Rules (Caller Must Enforce)

Before accepting an agent's conclusion, the caller (usually the `generate-document` orchestrator) must:

1. **Validate that the JSON appendix exists and is parseable.**
2. **Validate that `agent` matches the invoked agent.**
3. **Validate that all `required_answers` have `answered=true`.**
4. **Validate artifact field presence by agent type.**

Failure handling strategy:

- **First failure**: Append an in-place follow-up question (only request the missing fields/questions; do not rewrite the entire output).
- **Second failure**: Treat as agent invocation failure and enter the skill's block/degrade strategy (record evidence, notify, recovery point).

## 4. Validation Script Provided by This Repository

The repository provides `skills/implement-code/scripts/validate-agent-output.js` for quick gate validation of the JSON appendix:

```bash
node skills/implement-code/scripts/validate-agent-output.js --agent docs-retriever --file /path/to/output.txt
```

This script validates only "contract structure and required-answers coverage"; it does not validate content truthfulness. Truthfulness is still governed by `shared/evidence-and-uncertainty.md` and the upstream evidence chain.
