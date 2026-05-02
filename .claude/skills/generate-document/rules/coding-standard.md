---
paths:
  - "src/**/*.js"
  - "src/**/*.ts"
  - "components/**/*.js"
---

# Coding Standard

## Syntax Standards

- ES6+, prefer `const`; use `let` for reassignment; avoid `var`
- 4-space indent, semicolons at end of statements
- Single quotes `'`, template strings `${}` for concatenation
- Object literal shorthand, spread operator, destructuring
- Prefer arrow functions; use `async/await` for async

## Naming Conventions

- Variables/functions: camelCase; booleans: `is`/`has`/`can`/`should` prefix
- Function prefixes: `get`/`set`/`load`/`save`/`create`/`update`/`delete`/`handle`/`toggle`/`init`/`reset`
- Component names/files: PascalCase
- Constants: UPPER_SNAKE_CASE
- Utility files: camelCase; style files: kebab-case

## Comments and File Organization

- File top contains purpose comment; public functions have JSDoc
- Inline comments explain "why" not "what"
- Tags: `TODO`/`FIXME`/`HACK`/`NOTE`/`DEPRECATED`
- Import order: external libs → core utils → project utils → core services → local modules
- Prefer named exports; single file should not exceed 500 lines

## Vue 3 Composition API

- Use Composition API, state defined with `ref` (not `reactive`)
- State created via factory functions, always access via `.value`
- Do not destructure refs; use `Vue.computed` for computed properties

## State Management

- Use factory pattern to create Store
- Operation modules use factory functions, receiving dependencies as parameters
- Compose all method modules in `useMethods.js`

## Component Development

- Three files: `index.js`/`index.css`/`template.html`
- Use `registerGlobalComponent` to register components
- Props must define types; use `emits` to declare events
- Components register on `window` and trigger Loaded event

## Error Handling

- Code that may throw must be wrapped with `safeExecute`/`safeExecuteAsync`
- Use `createError` to create standardized error objects
- Use `showErrorMessage`/`showSuccessMessage` to display messages
- Use `safeGet`/`safeGetPath` for safe object property access

## Module Design

- Single responsibility; use factory function pattern for easy dependency injection and testing
- Group related methods together with common prefixes
- Use `window` exposure cautiously, only for features needing global access, with try-catch protection
