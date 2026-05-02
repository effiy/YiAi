# wework-bot-reliability-improvement

> **Document Version**: v1.0 | **Last Updated**: 2026-05-02 | **Maintainer**: kimi-k2.6 | **Tool**: Claude Code
>
> **Related Documents**: [Requirement Tasks](./02_requirement-tasks.md) | [Design Document](./03_design-document.md) | [Usage Document](./04_usage-document.md) | [CLAUDE.md](../../CLAUDE.md)

[Feature Overview](#feature-overview) | [User Stories](#user-stories) | [Acceptance Criteria](#acceptance-criteria) | [Feature Details](#feature-details)

---

## Feature Overview

The `wework-bot` skill is responsible for sending WeChat Work (WeCom) bot notifications at the end of `generate-document` and `implement-code` pipelines. During the MCP service transformation closure on 2026-04-30, `wework-bot` failed with a `502 Bad Gateway` error, causing the delivery closure notification to be lost. This feature adds a pre-flight health check and exponential-backoff retry mechanism to the `send-message.js` script, ensuring notification reliability even when the gateway or network is temporarily unstable.

**Scope**: Modify `.claude/skills/wework-bot/scripts/send-message.js` and `.claude/skills/wework-bot/config.json` to support health-check and retry logic. No changes to the message format or skill contract.

**Non-goals**: Changing the message payload schema, adding new notification channels, or modifying `import-docs` behavior.

- 🎯 **Goal**: Guarantee notification delivery or explicit failure logging
- ⚡ **Impact**: Prevents silent notification drops during pipeline closures
- 📖 **Clarity**: All retry attempts and final status are archived locally

---

## User Stories and Feature Requirements

**Priority**: 🔴 P0 | 🟡 P1 | 🟢 P2

**One user story corresponds to one `docs/<feature-name>/` numbered set (01–05, 07).**

| User Story | Acceptance Criteria | Process-Generated Documents | Output Smart Documents |
|------------|---------------------|----------------------------|------------------------|
| 🔴 As a DevOps operator, I want `wework-bot` to perform a lightweight health check before sending a notification and retry up to N times on transient failures, so that pipeline closure notifications are reliably delivered or explicitly logged as failed.<br/><br/>**Main Operation Scenarios**:<br/>- Health check passes, message sends successfully on first attempt<br/>- Health check fails, retry succeeds within max attempts<br/>- All retries exhausted, failure is logged with explicit fallback instruction | 1. `send-message.js` performs a HEAD/GET health check to the gateway before POST (P0)<br/>2. On 5xx or network errors, the script retries with exponential backoff up to 3 times (P0)<br/>3. Final failure writes a structured log entry to `docs/weekly/<week>/notify-failures.md` (P0)<br/>4. Retry parameters (max attempts, base delay) are configurable via `config.json` (P1)<br/>5. Success archive still writes to `messages.md` as before (P0) | [Requirement Tasks](./02_requirement-tasks.md)<br/>[Design Document](./03_design-document.md)<br/>[Project Report](./07_project-report.md) | [Generate Document Skill](../../.claude/skills/generate-document/SKILL.md)<br/>[Requirement Document Specification](../../.claude/skills/generate-document/rules/requirement-document.md)<br/>[Requirement Document Template](../../.claude/skills/generate-document/templates/requirement-document.md)<br/>[Requirement Document Checklist](../../.claude/skills/generate-document/checklists/requirement-document.md) |

---

## Document Specifications

- One numbered set corresponds to one user story
- Anti-hallucination: content that cannot be determined from repository facts/upstream write `> Pending confirmation (reason: …)`

---

## Acceptance Criteria

### P0 — Core (cannot release without)

1. `send-message.js` performs a health check request before the main POST
2. Retry with exponential backoff (max 3 attempts) on 5xx / network errors
3. Failure after all retries produces a structured log with timestamp, error code, and fallback instruction
4. Existing success archiving behavior (`messages.md`, `key-notes.md`) remains unchanged

### P1 — Important (recommended)

5. Retry configuration (max retries, base delay ms) is externalized to `config.json`
6. CLI flag `--skip-health-check` allows bypassing health check for emergency manual sends

### P2 — Nice-to-have

7. Circuit breaker pattern: after 3 consecutive failures within 5 minutes, skip health checks for 60 seconds

---

## Feature Details

### Health Check Before Send

- **Description**: Before POSTing the message payload, send a lightweight HEAD request to the gateway API URL to confirm reachability.
- **Boundaries**: Health check failure does not block the message send; it only triggers the retry-aware path.
- **Value**: Detects gateway outages before wasting a full message payload attempt.

### Exponential Backoff Retry

- **Description**: On HTTP 5xx, `ECONNREFUSED`, `ETIMEDOUT`, or `ECONNRESET`, wait `baseDelay * 2^attempt` ms and retry.
- **Boundaries**: Does not retry on 4xx client errors (except 429 Too Many Requests).
- **Value**: Recovers from transient network partitions and gateway instability.

### Structured Failure Log

- **Description**: When all retries are exhausted, append a structured markdown block to `docs/weekly/<week>/notify-failures.md` containing timestamp, agent, robot, HTTP status, error message, and a fallback instruction.
- **Boundaries**: Does not attempt alternative notification channels.
- **Value**: Creates an auditable record and explicit next-step instruction for operators.

---

## Usage Scenario Examples

### Scenario 1: Healthy gateway, single attempt success

- **Background**: Pipeline completes normally; gateway is healthy.
- **Operation**: `import-docs` succeeds → `wework-bot` sends completion notification.
- **Result**: Health check returns 200 within 500ms; message POST succeeds; archive written to `messages.md`.
- 📋 **Verification**: Check `messages.md` for the new entry.

### Scenario 2: Gateway 502, retry succeeds

- **Background**: Gateway experiences a transient 502 during peak load.
- **Operation**: `wework-bot` health check detects latency; first POST receives 502.
- **Result**: Script waits 1000ms, retries; second POST succeeds with 200.
- 📋 **Verification**: Console output shows retry count; `messages.md` contains final success.

### Scenario 3: Persistent outage, explicit failure log

- **Background**: Gateway is down for >10 seconds.
- **Operation**: Three POST attempts all fail with 502.
- **Result**: After third failure, script exits with code 1 and writes entry to `notify-failures.md`.
- 📋 **Verification**: `notify-failures.md` contains structured failure record with fallback instruction.

## Postscript: Future Planning & Improvements

- Consider extending retry logic to `import-docs` sync step for end-to-end pipeline resilience.
- Evaluate migrating from Node.js `https` to `fetch` with native `AbortSignal` for cleaner timeout handling.
