# wework-bot-reliability-improvement — Usage Document

> **Document Version**: v1.0 | **Last Updated**: 2026-05-02 | **Maintainer**: kimi-k2.6

## Usage Overview

This document describes how operators and pipeline orchestrators interact with the hardened `wework-bot` sender after the reliability improvements are deployed.

## Normal Usage

No changes to the standard invocation pattern:

```bash
API_X_TOKEN=*** node .claude/skills/wework-bot/scripts/send-message.js \
  --agent implement-code \
  -f ./tmp/wework-body.md
```

The script now automatically:
1. Performs a HEAD health check to the gateway
2. Sends the message
3. Retries up to 3 times on 5xx or network errors
4. Archives success to `docs/weekly/<week>/messages.md`

## Emergency Bypass

To skip the health check (e.g., when the health endpoint is known to be flaky but POST works):

```bash
API_X_TOKEN=*** node .claude/skills/wework-bot/scripts/send-message.js \
  --agent implement-code \
  --skip-health-check \
  -f ./tmp/wework-body.md
```

## Failure Investigation

If the script exits with code 1:

1. Check stderr for the failure reason and fallback instruction.
2. Inspect `docs/weekly/<week>/notify-failures.md` for the structured failure record.
3. Verify gateway health manually:
   ```bash
   curl -I https://api.effiy.cn/wework/send-message
   ```
4. Re-run the script after recovery.

## Configuration Tuning

Edit `.claude/skills/wework-bot/config.json` to adjust retry behavior:

```json
{
  "default_robot": "general",
  "api_url": "https://api.effiy.cn/wework/send-message",
  "retry": {
    "maxRetries": 3,
    "baseDelayMs": 1000
  },
  "robots": { ... }
}
```

| Field | Default | Description |
|-------|---------|-------------|
| `maxRetries` | 3 | Maximum retry attempts after the first failure |
| `baseDelayMs` | 1000 | Base delay in milliseconds; actual delay = `baseDelayMs * 2^attempt` |

## Postscript: Future Planning & Improvements

- Document advanced circuit breaker configuration when implemented.
