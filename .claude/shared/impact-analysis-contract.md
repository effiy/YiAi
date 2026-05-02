# Full-Project Impact Analysis Contract

> Shared impact-analysis口径 for `generate-document` and `implement-code`.

## Applicable Stages

| Stage | Consumer | Goal |
|-------|----------|------|
| Planning | `generate-document` | Identify affected modules, dependencies, and verification scope from upstream documents and existing code |
| Pre-implementation | `implement-code` stage 3 | Review proposed change points as an actionable list, confirm no missing dependencies |
| Post-implementation | `implement-code` stage 4/6 | Regression search on real diff, confirm sync-modification items are handled |

## Core Principles

1. **Full-project scope**: Search the entire repository by default, not just `src/` or the current module.
2. **Dependency graph closure**: Every change point must trace "depends on whom, whom depends on it" until the impact chain closes or the stop reason is explicitly stated.
3. **Reverse-dependency priority**: Before deleting/renaming/modifying a public interface, prove all callers are covered.
4. **Transitive impact required**: If a direct hit serves as a secondary API, barrel export, global registration, etc., continue tracing.
5. **Facts come from tools**: Reference relationships must come from actual search/file reads; do not fill from memory.
6. **Misses must be recorded**: Every search term must be logged; when there are no hits, write "no references found" and explain the implication.
7. **Planning and implementation cross-check**: `generate-document` provides the forecast; `implement-code` must re-check before and after real changes.

## Search Scope

**Include**: source code (src/, components, Store, composables, services, utils, styles), tests (tests/), docs (docs/), .claude/ rules, configuration and build (package.json, routing, CI, aliases), project-root run/build related files.

**Exclude**: node_modules/, dist/, build/, .git/, lock files, binary assets.

## Required Dimensions

| Dimension | Closure Standard |
|-----------|-----------------|
| Direct references | Every search term has a hit or a "no references found" record |
| Upstream dependencies | Upstream change risks are labeled (sync modify / keep compatible / verify only) |
| Reverse dependencies | All caller disposition methods are explicit |
| Transitive dependencies | Secondary+ impacts are closed or the stop reason is stated |
| Export chain | Export entry and all import sides are consistent |
| Registration chain | Registration point, consumption point, and registration order are verified |
| Data flow | Payload / return fields are consistent with all consumers |
| Types and contracts | Types, doc examples, and mocks are consistent with implementation |
| Style impact | Templates, :class, and classList are all covered |
| Tests and docs | Tests and docs to be added/updated/regressed are listed for disposition |
| Configuration and build | Local run, build, and CI have no broken links |
| External dependencies | New or upgraded dependencies have source, purpose, risk, and fallback strategy |

## Analysis Steps

1. List all proposed change points: files, exports, functions, components, Store, routes, events, CSS, configuration, dependency packages.
2. Build a search-term set for each change point: name, alias, path, tag name, event name, route name, string key, CSS token, env var name, package name.
3. Search the change point itself first, then export entry, registration entry, and public aggregation entry.
4. Full-project search each term, recording hit file, line number, reference method, impact level, and evidence.
5. Determine whether direct hits have secondary impact (further export/registration/forwarding/test dependency).
6. Continue searching secondary impact until the chain closes; state the reason when stopping.
7. Label disposition method: sync modify, keep compatible, supplement verification, manual review, no action needed.
8. Re-run steps 2–7 with real diff after implementation.

## Output Format

Must contain four parts (fields must not be missing):

1. **Search-term and change-point list**: change point / type / search term / source / notes
2. **Change-point impact chain**: change point / search term / hit file / reference method / impact level / dependency direction / disposition method / closure status / explanation
3. **Dependency closure summary**: change point / upstream verified / reverse verified / transitive closed / tests/docs/config covered / conclusion
4. **Uncovered risks**: risk source / reason / impact / mitigation

## P0 Gate

- Do not generate design conclusions or start implementation before completing the full-project search.
- Do not claim impact analysis is complete without outputting the search-term and change-point list.
- Do not delete/rename/modify public interfaces without analyzing upstream/reverse/transitive dependencies.
- Do not modify Store/events/routes/global components/build configuration without analyzing export chains, registration chains, tests, docs, and configuration impact.
- When "sync modify" or "block" items are found unhandled, write the block reason or pending list.
- Do not enter final summary without regression search using real diff after implementation.
