---
name: verification-loop
description: |
  Execute comprehensive verification for build, integration, deployment, and other
  non-UI scenarios. Pre-flight checks ensure one-shot pass rather than retrying
  after failure.
user_invocable: true
lifecycle: default-pipeline
---

# verification-loop

## Core Philosophy

**Rely on preparation, not retries.** Before executing verification commands, identify all issues that could cause failure and fix them; execution is final confirmation, not a debugging entry.

## Input

- **Verification target**: such as `npm run build`, `Vite bundling` (required)
- **Context documents**: design document/requirement task paths (optional)
- **Environment info**: Node version, package manager (optional, auto-read)

## Pre-flight: MCP Availability Probe

Before executing any stage, check MCP availability. **Silent degradation is prohibited:**

| Verification Scenario | Required MCP |
|-----------------------|-------------|
| Local file read/write/download verification | `filesystem` |
| Pure build/lint/type check | No MCP needed |

Probe result decisions:
- Required tool ❌ and no fallback → ⛔ Stop, prompt to configure and retry

## Workflow (4 phases, sequential execution)

### Phase 1: Environment Snapshot (no command execution)

Statically read `package.json` (script names, dependency versions), build configs (vite/tsconfig/eslint), `.nvmrc`, design document constraints.

**Block**: `package.json` does not exist or target script does not exist → stop

### Phase 2: Static Pre-flight (no build execution)

| Pre-flight Item | Common Failure Causes |
|-----------------|----------------------|
| Dependency integrity | Missing packages, version mismatch |
| TypeScript types | Type incompatibility, missing declaration files |
| Import paths | Path spelling errors, deleted files |
| Environment variables | Missing required variables |
| Lint rules | Format errors, unused variables |
| Known constraints | Design document conventions not implemented |

**Block**: blocking items found (e.g., import path does not exist) → fix first, then enter Phase 3

### Phase 3: Environment Alignment Confirmation

Current Node version satisfies `engines.node` / `.nvmrc`; package manager is consistent.

**Block**: misaligned → give alignment command, wait for execution before continuing

### Phase 4: One-shot Execution + Result Assertion

After all pre-flight passes, execute verification command, **only once**:

| Verification Item | Pass Condition |
|-------------------|---------------|
| Dependency install | exit code 0, no peer dep errors |
| Type check | exit code 0 |
| Lint | exit code 0 |
| Build | exit code 0, output directory non-empty |
| P0 unit tests | exit code 0 |
| UI/E2E | Equivalent scriptable automation executed, all P0 items pass |

Execution failure: no retry → parse error output → give "one-time fix checklist" (root cause + operation + re-entry phase)

## Usage Rules

- Pre-flight probe with blocking items prohibits entering Phase 1; Phase 1-3 with blocking items prohibits entering Phase 4
- Verification command names must be taken from `package.json` scripts, no hard-coding
- When command does not exist, output "script <name> does not exist, skipping"
- Phase 4 failure does not auto-retry; give fix checklist for caller decision
- automation degradation must be labeled ⚠️, cannot present as full pass
