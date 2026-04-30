# wework-bot 快速索引

`wework-bot` 发送企业微信机器人通知，主要服务 `generate-document` / `implement-code` 的监控预警和阶段通知。真源在 `SKILL.md`。

## 快速开始

```bash
# 设置 token（一次性）
export API_X_TOKEN=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# 短正文
API_X_TOKEN=*** node .claude/skills/wework-bot/scripts/send-message.js \
  --agent implement-code \
  --content $'📣 阶段通知\n🎯 结论：冒烟通过'

# 长正文（推荐）
API_X_TOKEN=*** node .claude/skills/wework-bot/scripts/send-message.js \
  -f ./notify-body.md
```

## 常用参数

- `--agent`：按配置映射选择机器人（推荐）
- `--content` / `-c`、`--content-file` / `-f`：完整正文（二选一）

## 文件职责

| 文件 | 职责 |
|------|------|
| `SKILL.md` | 何时使用、输入参数、工作流程 |
| `rules/message-contract.md` | 消息格式、安全、调用契约 |
| `config.json` | 默认配置（已提交） |
| `scripts/send-message.js` | 发送脚本 |