# Code Implementation Spec

> Constrains all coding behavior in implement-code stage 4 (writing project code). Co-constrained with `../../generate-document/rules/`, **this spec takes precedence**.

---

## 1. Core Constraints (P0)

| # | Constraint |
|---|------------|
| C0-1 | No project code may be written before dynamic check gates pass (Gate A see [`implement-code-testing.md`](./implement-code-testing.md)) |
| C0-2 | Every line of code must be traceable to a design-document module, interface, or impact-chain record |
| C0-3 | No new files/directories not mentioned in the design document (new additions must be annotated with reason) |
| C0-4 | P0 syntax errors must be eliminated after implementation |
| C0-5 | `data-testid` must be added to real components after implementation (consistent with test page) |
| C0-6 | Must pass stage 6 smoke test before entering stage 7 |
| C0-7 | Before deleting/renaming/modifying public interfaces, full-project impact-chain closure analysis must be completed |
| C0-8 | Shared vs. application component layering must follow project conventions; when no convention exists, it must be explicit in the design document |

---

## 2. Project-Specific Constraints

- **Entry initialization**: Follow the project's existing `initApp` pattern; do not introduce new patterns
- **Hooks factory**: `store.js` (Vue.ref) → `useComputed.js` (Vue.computed) → `useMethods.js` (domain methods);禁止使用 Vue.reactive directly
- **Shared component registration**: Export/register per project convention, maintain unified entry
- **Code structure**: Follow `../../generate-document/rules/code-structure.md`

---

## 3. Implementation Order

1. Hooks/state layer → store → useComputed → useMethods
2. Shared components → component files + export entry
3. Application components → component files + data-testid
4. View entry → initialize/mount per project convention
5. Entry confirmation → index.html references correct

---

## 4. data-testid Porting

All `data-testid` in the test page must appear verbatim in real components, without renaming or omission. After completion, confirm against the prototype page element list one by one.

---

## 5. Implementation Checklist

**Before implementation (all must pass before coding)**:
- All module paths in design document are confirmed
- Shared/application component placement paths are confirmed per project convention
- Hooks three-file pattern is complete (store / useComputed / useMethods)
- `../../../shared/impact-analysis-contract.md` has been read
- Full-project impact-chain closure analysis is completed for every change point

**After each module completes**:
- P0 syntax errors are eliminated
- data-testid is complete
- Shared component exports and registration are consistent
- Entry initialization/mount is complete
- Full-project impact-chain regression verification (rebuild search terms based on real diff)

---

## 6. Prohibitions

- Introducing new directories/path conventions without confirming project structure
- Writing new code without reading existing code
- Skipping hooks factory pattern and writing reactive directly
- Skipping data-testid porting
- Entering next stage with P0 syntax errors unaddressed
