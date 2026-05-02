# wework-bot-reliability-improvement — Dynamic Checklist

> **Document Version**: v1.0 | **Last Updated**: 2026-05-02 | **Maintainer**: kimi-k2.6
> **Preconditions**: `02_requirement-tasks.md` and `03_design-document.md` exist and contain 3 main operation scenarios.

---

## General Check

- [ ] Document header is complete with version, date, maintainer
- [ ] Required chapters are present: General Check / Main Scenario Verification / Code Quality Check / Test Check / Check Summary
- [ ] Scenario count equals requirement-tasks scenario count (3 scenarios)
- [ ] Every scenario links to corresponding anchors in requirement-tasks and design-document

---

## Main Scenario Verification

### Scenario 1: Healthy gateway, single attempt success

| Precondition | Status |
|--------------|--------|
| `API_X_TOKEN` is set in environment | ⏳ Pending |
| `config.json` exists and is valid JSON | ⏳ Pending |
| Gateway returns 200 for HEAD and POST | ⏳ Pending |

| Operation Step | Verification Method | Status |
|----------------|---------------------|--------|
| Invoke `send-message.js --agent generate-document -f body.md` | Console output | ⏳ Pending |
| Observe health check HEAD request | Console or network log | ⏳ Pending |
| Observe POST success (HTTP 200) | Console status line | ⏳ Pending |
| Verify `messages.md` archive | `cat docs/weekly/<week>/messages.md` | ⏳ Pending |

| Expected Result | Status |
|-----------------|--------|
| Script exits with code 0 | ⏳ Pending |
| `messages.md` contains new entry with timestamp and agent | ⏳ Pending |
| No retry warnings in stderr | ⏳ Pending |

- **Requirement-tasks anchor**: [Scenario 1](./02_requirement-tasks.md#scenario-1-healthy-gateway-single-attempt-success)
- **Design-document anchor**: [Scenario 1 Implementation](./03_design-document.md#scenario-1-healthy-gateway-single-attempt-success)

### Scenario 2: Gateway 502, retry succeeds

| Precondition | Status |
|--------------|--------|
| Gateway intermittently returns 502 | ⏳ Pending |
| `config.json` retry config allows ≥1 retry | ⏳ Pending |

| Operation Step | Verification Method | Status |
|----------------|---------------------|--------|
| Trigger send during gateway 502 window | Console output | ⏳ Pending |
| Observe first POST returns 502 | Console status line | ⏳ Pending |
| Observe retry delay message in stderr | Console output | ⏳ Pending |
| Observe second POST returns 200 | Console status line | ⏳ Pending |

| Expected Result | Status |
|-----------------|--------|
| Script exits with code 0 | ⏳ Pending |
| stderr contains retry count (e.g., "Retry 1/3 after 1000ms...") | ⏳ Pending |
| `messages.md` contains exactly one success entry (no duplicates) | ⏳ Pending |

- **Requirement-tasks anchor**: [Scenario 2](./02_requirement-tasks.md#scenario-2-gateway-502-retry-succeeds)
- **Design-document anchor**: [Scenario 2 Implementation](./03_design-document.md#scenario-2-gateway-502-retry-succeeds)

### Scenario 3: Persistent outage, explicit failure log

| Precondition | Status |
|--------------|--------|
| Gateway is down or consistently returns 5xx | ⏳ Pending |
| `maxRetries` in config is ≥1 | ⏳ Pending |

| Operation Step | Verification Method | Status |
|----------------|---------------------|--------|
| Trigger send while gateway is down | Console output | ⏳ Pending |
| Observe all POST attempts fail | Console status line | ⏳ Pending |
| Observe final failure message in stderr | Console output | ⏳ Pending |
| Verify `notify-failures.md` archive | `cat docs/weekly/<week>/notify-failures.md` | ⏳ Pending |

| Expected Result | Status |
|-----------------|--------|
| Script exits with code 1 | ⏳ Pending |
| `notify-failures.md` contains structured failure block | ⏳ Pending |
| Failure block includes: timestamp, status, reason, attempts, fallback instruction | ⏳ Pending |

- **Requirement-tasks anchor**: [Scenario 3](./02_requirement-tasks.md#scenario-3-persistent-outage-explicit-failure-log)
- **Design-document anchor**: [Scenario 3 Implementation](./03_design-document.md#scenario-3-persistent-outage-explicit-failure-log)

---

## Code Quality Check

- [ ] All modified files have been reviewed for style consistency
- [ ] No secrets (tokens, webhook URLs) committed in code
- [ ] Error handling covers network errors, file I/O errors, and config parsing errors
- [ ] No `console.log` leakage in production paths (only `console.warn` for retries and `console.error` for failures)

---

## Test Check

- [ ] Mock gateway test: 502 twice then 200 → verify retry succeeds
- [ ] Mock gateway test: persistent 502 → verify failure archive written
- [ ] Config fallback test: missing `retry` section → verify defaults used
- [ ] `--skip-health-check` test: verify HEAD request is bypassed
- [ ] Existing success archive behavior unchanged

---

## Check Summary

### P0 Items

| Scenario | Items | Passed | Pass Rate |
|----------|-------|--------|-----------|
| Scenario 1 | 4 | 0 | 0% |
| Scenario 2 | 4 | 0 | 0% |
| Scenario 3 | 4 | 0 | 0% |
| Code Quality | 4 | 0 | 0% |
| Test Check | 5 | 0 | 0% |

### P1 Items

| Item | Status |
|------|--------|
| Retry configuration externalized | ⏳ Pending |
| `--skip-health-check` flag works | ⏳ Pending |

### P2 Items

| Item | Status |
|------|--------|
| Circuit breaker pattern implemented | ⏳ Pending |

### Overall Conclusion

⏳ All verification items are pending. Execute tests and mark results after implementation.

## Postscript: Future Planning & Improvements

- Add automated mock-gateway test script to CI when CI is introduced.
