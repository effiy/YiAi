调用 `wework-bot` 技能发送企业微信机器人消息。

参数：`$ARGUMENTS`

执行要求：
- 用户意图是发群通知时必须执行 `send-message.js` 真实发送，不得只停留在草稿
- 长文案优先 `--content-file`，短文案可用 `--content`；正文须按 `message-contract` 对齐
- 与 `generate-document`/`implement-code` 联动时：先 `import-docs`，再 `wework-bot`
- 完成通知中的 `☁️ 文档同步`须引用 `import-docs` 真实统计，不得写占位数字
- 不得泄露 `API_X_TOKEN`、webhook 明文