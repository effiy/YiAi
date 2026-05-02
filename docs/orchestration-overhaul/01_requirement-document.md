# Orchestration Overhaul

> **Document Version**: v1.0 | **Last Updated**: 2026-05-03 | **Maintainer**: Claude | **Tool**: Claude Code
>
> **Related Documents**: [Requirement Tasks](./02_requirement-tasks.md) | [Design Document](./03_design-document.md) | [Usage Document](./04_usage-document.md) | [CLAUDE.md](../../CLAUDE.md)
>

[Feature Overview](#feature-overview) | [User Stories](#user-stories) | [Acceptance Criteria](#acceptance-criteria) | [Feature Details](#feature-details)

---

## Feature Overview

Orchestration Overhaul introduces a lightweight execution orchestration layer into YiAi, replacing ad-hoc module calls with deterministic pipelines. It adds a Harness for deterministic audit scoring of every execution step, hardens launcher compatibility across direct-import and subprocess modes, and upgrades loop prevention from a single depth guard to a 5-layer defense-in-depth stack. The goal is to make dynamic module execution predictable, observable, and safe at scale.

🎯 **Deterministic Execution**: Pipeline definitions produce reproducible results with deterministic audit scoring.

⚡ **Launcher Hardening**: Unified launcher abstraction supports direct import, subprocess, and future remote workers without caller changes.

📖 **5-Layer Loop Guard**: Defense-in-depth against infinite recursion and cyclic orchestration graphs.

---

## User Stories and Feature Requirements

| Priority | User Story | Acceptance Criteria | Documents |
|----------|------------|---------------------|-----------|
| 🔴 P0 | As a system operator, I want orchestration pipelines with deterministic audit scoring, so that module execution chains are reproducible and quality is measured consistently. | 1. Pipeline JSON/YAML definition → deterministic execution order<br>2. Harness scores every step with deterministic rubric<br>3. Scores persisted to state_records<br>4. Failed step halts pipeline and triggers audit | [Requirement Tasks](./02_requirement-tasks.md)<br>[Design Document](./03_design-document.md)<br>[Project Report](./07_project-report.md) |
| 🔴 P0 | As a platform engineer, I want a hardened launcher abstraction, so that execution mode can switch between direct import and subprocess without route changes. | 1. Launcher interface covers direct + subprocess<br>2. Config-driven mode selection<br>3. Launcher health check endpoint<br>4. Graceful fallback on launcher failure | [Requirement Tasks](./02_requirement-tasks.md)<br>[Design Document](./03_design-document.md)<br>[Project Report](./07_project-report.md) |
| 🟡 P1 | As a security engineer, I want 5-layer loop prevention, so that recursive or cyclic orchestration graphs cannot stack-overflow or deadlock the process. | 1. HTTP middleware layer<br>2. Route layer guard<br>3. Executor layer guard<br>4. Module-level guard<br>5. Graph cycle detection in pipeline definitions<br>6. Any layer triggers 508 or halts pipeline | [Requirement Tasks](./02_requirement-tasks.md)<br>[Design Document](./03_design-document.md)<br>[Project Report](./07_project-report.md) |

---

## Document Specifications

1. **Orchestration Pipeline**: Defined as a DAG of steps, each step referencing a `module_path:function_name` and parameters. Pipeline runner executes topologically sorted steps.
2. **Harness Audit Scoring**: Each step output is scored against a rubric (success, partial, failure) with a numeric score (0-100). The score is deterministic given the same input and output.
3. **Launcher Compatibility**: `DirectLauncher` uses `importlib` + async call; `SubprocessLauncher` uses `asyncio.create_subprocess_exec`; both implement `BaseLauncher` interface.
4. **5-Layer Loop Prevention**:
   - L1: HTTP ThrottleMiddleware (existing)
   - L2: Route-level ReentrancyGuard (existing)
   - L3: Executor-level ReentrancyGuard (existing)
   - L4: Module-level call graph cycle detector (new)
   - L5: Pipeline DAG cycle detector (new)

---

## Acceptance Criteria

### P0

- [ ] Pipeline definition can be submitted via API and executed deterministically.
- [ ] Harness scores every step with deterministic 0-100 score.
- [ ] Launcher abstraction supports direct and subprocess modes via config.
- [ ] Failed launcher mode falls back safely without crashing the request.
- [ ] 5-layer loop prevention is active and any layer can halt recursion.

### P1

- [ ] Pipeline execution status is queryable via API.
- [ ] Harness scores are filterable and exportable.
- [ ] Launcher health endpoint shows active mode and last error.
- [ ] Pipeline DAG validation rejects cyclic definitions before execution.

### P2

- [ ] Visual pipeline definition editor (future).
- [ ] Remote worker launcher mode (future).
- [ ] Adaptive scoring rubrics based on historical data (future).

---

## Feature Details

### Orchestration Pipeline Engine

A pipeline is a directed acyclic graph (DAG) of execution steps. The orchestrator resolves dependencies, executes steps in topological order, and aggregates results. Each step's output can be referenced as input to downstream steps via variable interpolation.

**Boundaries**: Pipeline definitions are limited to 100 steps and 10 depth levels. Execution timeout per step is configurable (default 300s).

**Value**: Eliminates ad-hoc chaining logic in client code; centralizes retry, timeout, and scoring policies.

### Harness Audit Scoring

The Harness evaluates step outputs using a configurable rubric. A default rubric assigns:
- 100 if output is non-empty dict/list and no exception
- 50 if output is empty but no exception
- 0 if exception or timeout

Scores are persisted to the state store with `record_type="audit_score"`.

**Boundaries**: Scoring is applied only to synchronous final outputs; streaming generators are scored on completion status only.

**Value**: Provides quantitative quality metrics for module reliability and regression detection.

### Launcher Compatibility

The launcher abstraction decouples the execution API from the invocation mechanism. `BaseLauncher` defines `launch(module_path, function_name, parameters) -> Result`. Two implementations are provided:
- `DirectLauncher`: Fast, in-process, suitable for trusted code.
- `SubprocessLauncher`: Isolated, slower, suitable for untrusted or resource-heavy code.

**Boundaries**: Launcher selection is global per deployment, not per-request, to avoid confusion. Dynamic per-request selection is P2.

**Value**: Simplifies ops changes (e.g., switch to subprocess for security hardening) without API changes.

### 5-Layer Loop Prevention

Building on the existing ReentrancyGuard (1 layer), the overhaul adds 4 additional layers:
- L1: HTTP ThrottleMiddleware prevents rapid-fire recursive HTTP calls.
- L2: Route-level ReentrancyGuard on `/execution` and `/orchestration/run`.
- L3: Executor-level ReentrancyGuard inside `execute_module`.
- L4: Module-level call graph tracker records `caller -> callee` edges per request context and rejects cycles.
- L5: Pipeline DAG validator rejects cyclic pipeline definitions at submit time.

**Boundaries**: L4 is request-scoped (ContextVar), not global. L5 is static validation only.

**Value**: Defense in depth ensures that even if one layer is bypassed, others catch the loop.

---

## Usage Scenario Examples

### Example 1: Running an Audit Pipeline

📋 **Background**: A data processing workflow needs to fetch RSS, summarize articles, and upload results.

🎨 **Operation**:
1. POST `/orchestration/pipelines` with a 3-step DAG definition.
2. POST `/orchestration/pipelines/{id}/run`.
3. GET `/orchestration/pipelines/{id}/status` to observe progress.
4. GET `/state/records?record_type=audit_score` to view harness scores.

📋 **Result**: Pipeline completes; each step scored; total pipeline score computed as average.

### Example 2: Switching Launcher Mode

📋 **Background**: Security review mandates subprocess isolation for all module execution.

🎨 **Operation**:
1. Update `config.yaml`: `orchestration_launcher_mode: subprocess`.
2. Restart server.
3. GET `/health/launcher` to verify active mode.
4. Run existing `/execution` calls unchanged.

📋 **Result**: All module executions now run in subprocesses; API contracts unchanged.

### Example 3: Detecting Cyclic Pipeline

📋 **Background**: A user accidentally defines step C depending on step A, while step A depends on step C.

🎨 **Operation**:
1. POST `/orchestration/pipelines` with cyclic definition.

📋 **Result**: API returns 400 with message `Cycle detected: A -> C -> A`.

---

## Postscript: Future Planning & Improvements

1. **Remote Worker Launcher**: Extend `BaseLauncher` with a `RemoteLauncher` that dispatches to Celery/RQ workers.
2. **Pipeline Visualization**: Generate Mermaid diagrams from pipeline definitions for documentation.
3. **Adaptive Rubrics**: Use historical harness scores to train ML-based quality predictors.
4. **Distributed Loop Detection**: Share L4 call graph state across instances via Redis for cluster-wide loop prevention.
