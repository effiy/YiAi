# Shared Component Development Contract

> Shared component development standards, serving as the shared interpretation layer for `doc-architect`, `code-reviewer`, and `implement-code`.

## 1. What Belongs in Shared Layer vs. Application Layer

| Type | Location | Criterion |
|------|----------|-----------|
| Cross-application shared components | `<shared>/components/` | Needed by at least 2 applications |
| Application-specific components | `<app>/components/` | Used only in a single application |
| General utility functions | `<shared>/utils/` | Do not depend on a specific application Store |
| Application-specific utilities | `<app>/utils/` | Depend on specific application state / context |

## 2. Three-File Structure

```
<shared>/components/<category>/<component-name>/
├── index.js       # Component logic (required)
├── template.html  # Component template (required)
└── index.css      # Component styles (optional)
```

- **index.js**: Use the project's existing component registration/export pattern (e.g. `registerGlobalComponent`). Props use object syntax (with type and default). Events emit via `$emit`.
- **template.html**: Standard HTML + Vue template syntax bindings.
- **index.css**: BEM naming with project prefix convention (e.g. `app-btn--primary`).

## 3. Barrel Export

If the project uses barrel export, shared components must be exported in a unified entry file to avoid omitting already-developed components.

## 4. Component Categories

| Category | Path | Description |
|----------|------|-------------|
| Common buttons | `<shared>/components/common/buttons/` | Button, IconButton |
| Common forms | `<shared>/components/common/forms/` | Input, Select, Checkbox |
| Common modals | `<shared>/components/common/modals/` | Modal, Dialog |
| Common data display | `<shared>/components/common/data-display/` | Table, Tooltip |
| Common feedback | `<shared>/components/common/feedback/` | Loading, EmptyState |
| Domain components | `<shared>/components/domain/` | Domain-specific (if shared) |

## 5. Integration with Application Entry

Application entry should explicitly declare/register required shared components during initialization (method per project convention).

## 6. Safe Execution

Async operations inside shared components should use the project's unified error-handling wrapper (e.g. `safeExecute`).

## 7. Checklist

- Component is placed under the shared layer path, not mixed with application layer.
- Three-file structure is complete.
- Barrel export is registered in unified entry (if used).
- Class names follow project BEM/prefix convention.
- Async operations use `safeExecute` wrapper.
- Props use object syntax.
- Events emit via `$emit`, do not directly mutate parent state.
