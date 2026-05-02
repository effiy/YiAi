---
paths:
  - "src/**/*.js"
---

# Code Structure Specification

## Directory Organization

```
<repo-root>/
├── .claude/        # Claude Code config and skills
├── <shared>/       # Shared modules (name per project reality)
│   ├── components/ # Shared components (optional)
│   ├── scripts/    # Scripts (import-docs, etc., optional)
│   ├── styles/     # Global styles (optional)
│   └── utils/      # Utility functions (optional)
├── docs/           # Project documentation
├── src/            # Application code
│   ├── core/       # Core config and services
│   └── views/      # Application views
├── index.html      # SPA entry
└── CLAUDE.md       # Project readme
```

## Core Architecture Patterns

### Entry Initialization Pattern

Projects typically have a unified entry initialization method (`initApp` / `createApp` / factory function, etc.). Follow the project reality.

### Hooks Factory Pattern

Each application view uses a three-file hooks pattern:

| File | Content | Caller |
|------|---------|--------|
| `hooks/store.js` | `createStore()` — returns `{ key: Vue.ref() }` | createBaseView |
| `hooks/useComputed.js` | `useComputed(store)` — returns `{ key: Vue.computed() }` | createBaseView |
| `hooks/useMethods.js` | `useMethods(store)` — returns `{ key: function }` | createBaseView |

Store internals can be split into operation modules.

### Module Import Convention

Use **absolute paths** for imports: `/src/views/appA/hooks/store.js`. Avoid relative paths.

## Application View Structure

```
src/views/<app>/
├── components/     # App-specific components
├── constants/      # Constants
├── hooks/          # Hooks factory
├── styles/         # App styles
├── utils/          # App utilities
├── index.html      # App HTML entry
└── index.js        # App JS entry (createBaseView)
```

## Checklist

- Shared layer and app layer placement rules are defined in project docs
- Hooks three-file pattern is complete (store.js / useComputed.js / useMethods.js)
- Use absolute paths for module imports
- Store uses `Vue.ref` factory, not direct reactive
- Operation modules use dependency injection pattern
- Methods are organized via useMethods combiner
- Components are globally registered and trigger Loaded event
