---
name: wework-bot
description: 发送企业微信机器人消息。generate-document / implement-code 完成/阻断/门禁异常时强制使用。
---

# wework-bot

## 定位

企业微信机器人通知技能：把阶段状态、阻断原因、验证结果推送到企业微信群机器人，支持按 agent 路由到不同机器人。

## 何时使用

- 用户要求把信息发到企微群/机器人
- 长流程需外部观测（阶段状态/阻断/门禁异常/验证结论）
- **链路强制**：`generate-document` / `implement-code` 完成/阻断/门禁异常必须通知，顺序：先 `import-docs`，再 `wework-bot`
- 不触发：用户只写文案草稿但明确不发送；目标是同步 docs（走 `import-docs`）

## 输入

| 参数 | 说明 |
|------|------|
| `API_X_TOKEN` | 必填，仅从系统环境变量读取 |
| `WEWORK_BOT_API_URL` | 可选，覆盖默认 API |
| `WEWORK_BOT_CONFIG` | 可选，路由 JSON 路径（默认仓库内 `config.json`） |
| `--agent` | 按 `config.agents` 映射到 robot（推荐） |
| `--robot` | 直接指定 robot 名（少用） |
| `--content` / `-c` | 完整正文字符串 |
| `--content-file` / `-f` | 从 UTF-8 文件读取正文（推荐长文案） |

webhook 仅在 `config.json` 中配置，无 CLI 传入。

## 工作流程

1. 组装消息：由 `message-pusher`（或等价流程）按电梯法则与契约写好完整正文
2. 选择机器人：`config.json` 按 `--agent` 或 `--robot` 解析 webhook；未指定时使用 `default_robot`
3. 校验凭据：`API_X_TOKEN` + webhook 来自配置
4. 发送：`node scripts/send-message.js --agent … --content-file …`
5. 汇总结果：根据 HTTP 状态码判断成功/失败

## 推送文案与反幻觉

- 需要系统核对事实时调用 `message-pusher` 代理
- 正文转义：字面 `\n` 改用 `--content-file` 或脚本 `normalizeMessageText` 归一化

## 消息格式（唯一真源）

全文契约见 `rules/message-contract.md`。核心约定：
- **摘要段**（分隔线之上）：约 10 行内可读清结论、影响、下一步
- **明细段**（分隔线之下）：给研发核对
- 摘要硬含：`🎯 结论` + `📝 描述` + `📌 范围` + `👉 下一步`
- 完成/阻断/门禁须含：`🌐 影响` + `📎 证据` + `⏱️ 会话`

## 运行示例

```bash
API_X_TOKEN=*** node .claude/skills/wework-bot/scripts/send-message.js \
  --agent implement-code \
  -f ./tmp/wework-body.md
```

## 门禁失败/失效强制通知

门禁未通过、未执行、缺证据、降级未记录 → 必须发送，摘要段须含结论、门禁名、原因、影响、恢复点。

## 会话中断强制通知

任何非正常结束必须发送，须说明流程/阶段、中断原因、影响范围、证据与恢复点。`⏱️ 会话` 一行合并耗时与用量。

## 安全约束

- 不得提交真实 X-Token、webhook URL 或 key
- 回复只展示脱敏摘要
- 完成通知为强制执行，其余场景默认不自动发送

## 支持文件

- `rules/message-contract.md`：消息格式、安全、调用契约
- `config.json`：默认配置（已提交）
- `scripts/send-message.js`：发送脚本