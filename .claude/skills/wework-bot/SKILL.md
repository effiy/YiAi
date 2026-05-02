---
name: wework-bot
description: |
  Send WeChat Work (WeCom) bot messages. Mandatory upon generate-document /
  implement-code completion, block, or gate failure.
user_invocable: true
lifecycle: default-pipeline
---

# wework-bot

## Positioning

WeChat Work bot notification skill: push stage status, block reasons, and verification results to WeChat Work group bots, supporting routing to different bots by agent.

## When to Use

- User requests sending information to WeChat group/bot
- Long process needs external observation (stage status/block/gate failure/verification conclusion)
- **Pipeline mandatory**: `generate-document` / `implement-code` completion/block/gate failure must notify, sequence: first `import-docs`, then `wework-bot`
- Do not trigger: user only writes draft copy but explicitly does not send; target is sync docs (use `import-docs`)

## Input

| Parameter | Description |
|-----------|-------------|
| `API_X_TOKEN` | Required, read only from system environment variables |
| `WEWORK_BOT_API_URL` | Optional, overrides default API |
| `WEWORK_BOT_CONFIG` | Optional, routing JSON path (defaults to in-repo `config.json`) |
| `--agent` | Map to robot via `config.agents` (recommended) |
| `--robot` | Directly specify robot name (rarely used) |
| `--content` / `-c` | Complete body string |
| `--content-file` / `-f` | Read body from UTF-8 file (recommended for long copy) |

Webhook is configured only in `config.json`, no CLI parameter.

## Workflow

1. Assemble message: write complete body by `message-pusher` (or equivalent flow) per elevator pitch and contract
2. Select bot: `config.json` resolves webhook via `--agent` or `--robot`; uses `default_robot` when unspecified
3. Validate credentials: `API_X_TOKEN` + webhook from config
4. Send: `node scripts/send-message.js --agent … --content-file …`
5. Summarize result: determine success/failure based on HTTP status code

## Push Copy and Anti-Hallucination

- Call `message-pusher` agent when system fact-checking is needed
- Body escaping: literal `\n` should use `--content-file` or script `normalizeMessageText` normalization

## Message Format (Single Source of Truth)

Full contract: `rules/message-contract.md`. Core conventions:
- **Summary segment** (above separator): ~10 lines to clearly read conclusion, impact, next steps
- **Detail segment** (below separator): for R&D verification
- Summary must contain: `🎯 Conclusion` + `📝 Description` + `📌 Scope` + `👉 Next Steps`
- Completion/block/gate must contain: `🌐 Impact` + `📎 Evidence` + `⏱️ Session`

## Example

```bash
API_X_TOKEN=*** node .claude/skills/wework-bot/scripts/send-message.js \
  --agent implement-code \
  -f ./tmp/wework-body.md
```

## Gate Failure/Invalidation Mandatory Notification

Gate not passed, not executed, missing evidence, or degradation not recorded → must send, summary must contain conclusion, gate name, reason, impact, recovery point.

## Session Interruption Mandatory Notification

Any abnormal termination must send, must explain process/stage, interruption reason, impact scope, evidence and recovery point. `⏱️ Session` line merges time and usage.

## Security Constraints

- Do not commit real X-Token, webhook URL, or key
- Replies only show desensitized summaries
- Completion notification is mandatory; other scenarios do not auto-send by default

## Supporting Files

- `rules/message-contract.md`: message format, security, call contract
- `config.json`: default config (committed)
- `scripts/send-message.js`: send script
