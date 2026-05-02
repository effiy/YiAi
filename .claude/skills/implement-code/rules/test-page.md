# Test Prototype Page Spec

> Prototype page structure and content requirements generated in implement-code stage 2.

---

## 1. Core Constraints

| ID | Constraint |
|----|------------|
| T0-1 | One prototype page per scenario: `tests/e2e/<feature-name>/pages/<scenario-name>/index.html` |
| T0-2 | Page contains all P0 operation step UI elements for that scenario in the dynamic checklist |
| T0-3 | All interactive elements carry `data-testid="<feature-name>-<element-description>"` |
| T0-4 | Page is accessible via `file://` or localhost (no login/route guard dependency) |
| T0-5 | Top-of-page comment explains user story number and checklist chapter |

---

## 2. data-testid Naming

| Element Type | Naming Pattern | Example |
|-------------|----------------|---------|
| Container | `<feature-name>-container` | `toolbar-container` |
| Button | `<feature-name>-<verb>-btn` | `toolbar-download-btn` |
| Input | `<feature-name>-<field>-input` | `toolbar-filename-input` |
| Result area | `<feature-name>-result` | `toolbar-result` |
| Error message | `<feature-name>-error-msg` | `toolbar-error-msg` |

---

## 3. Stub Behavior Constraints

**Allowed**: classList.add/remove, textContent set, disabled toggle, aria attribute set
**Prohibited**: fetch/XMLHttpRequest, framework import, domain logic functions exceeding 10 lines

---

## 4. Accessibility

- Dialog uses `role="dialog"` + `aria-modal="true"`
- Error hint uses `role="alert"`
- Icon buttons must have `aria-label`
