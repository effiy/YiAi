# Process Summary Spec

> Content and format of `06_process-summary.md`.

---

## 1. Core Constraints

| # | Constraint |
|---|------------|
| S0-1 | Save to `docs/<feature-name>/06_process-summary.md` |
| S0-2 | Must contain AI call flowchart and sequence diagram (actual path, not ideal path) |
| S0-3 | Must contain changed file list (path + type + associated module) |
| S0-4 | Must generate block version summary when blocked |
| S0-5 | Must write back implementation status to `01/02/03/04/05/07` |
| S0-6 | Normal completion must contain dynamic checklist final review (P0/P1/P2 statistics) |

---

## 2. Document Structure

| § | Title | Description |
|---|-------|-------------|
| §0 | Task Overview | Time, model, branch, final status |
| §1 | AI Call Flowchart | Mermaid flowchart |
| §2 | AI Call Sequence Diagram | Mermaid sequenceDiagram |
| §3 | Changed File List | Path, type (add/modify/delete), module, whether in tests/ |
| §4 | Verification Results | Gate report + dynamic checklist review |
| §5 | Status Write-Back Record | 01/02/03/04/05/07 write-back results |
| §6 | Open Issues and Follow-Up Suggestions | P1/P2 + self-improvement + executable next steps |
| §7 | Notification Record | wework-bot, import-docs |

---

## 3. Self-Improvement (Evidence-Driven)

Must produce improvement suggestion table for `.claude/`: category / problem / evidence / suggested path / minimum change point / verification method. Can only reference evidence positions already appearing in this summary.

---

## 4. Executable Next Steps

Each must contain: basis (reference §/file/check item) + verification method (command/checklist number/anchor); both are mandatory.

---

## 5. Block Version Summary

Simplified structure: block summary + already produced artifacts + block details + suggested recovery operations. Save to same path; overwritten by full version when recovery succeeds.

---

## 6. Prohibitions

- Adding nodes not actually called to the flowchart
- Omitting files from the change list
- Writing "completed" when dynamic checklist has unfinished items
- Terminating directly without generating summary when blocked
