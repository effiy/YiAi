调用 `wework-bot` 技能发送企业微信机器人消息。

```mermaid
graph LR
    A[/wework-bot] --> B[Assemble message body]
    B --> C[Resolve robot via agent/config]
    C --> D[Validate credentials]
    D --> E[Send via send-message.js]
    E --> F{HTTP status}
    F -->|200| G[Report success]
    F -->|error| H[Log failure + retry note]
```

参数: `$ARGUMENTS`

执行要求：
- 用户意图为发送群通知时，必须执行 `send-message.js` 真实发送；不得止步于草稿。
- 长文案使用 `--content-file`；短文案可用 `--content`。正文须符合 `message-contract`。
