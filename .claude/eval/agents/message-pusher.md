# message-pusher 评测示例（配合 wework-bot）

真源：`.claude/agents/message-pusher.md`；契约与脚本：`.claude/skills/wework-bot/rules/message-contract.md`、`.claude/skills/wework-bot/scripts/send-message.js`。

**评测定位**：聚焦写稿与事实对齐（Plan → 反幻觉 → 分行正文 → 交付参数/文件）。端到端真推送以 [skills/wework-bot.md](../skills/wework-bot.md) 为准。

**评测约束**：
1. 用户要求「推到群」时，须以 `send-message.js` 真实调用收尾——详见 wework-bot 评测约束
2. 真发前须体现先 Plan 后写稿，摘要段优先；禁止占位符与臆造数字进入推送载荷

---

## 成功判据（可观测）

| 维度 | 预期 |
|------|------|
| 流程类型 | 说明推送属于完成/阻断/门禁/阶段之一，指向证据路径 |
| 事实来源 | 列出或可回溯事实清单；缺项标为「需核对」而非编造 |
| 会话度量 | 完成/阻断/门禁类：`⏱️ 会话` 一行（耗时+用量）；缺数据写明「须核对」 |
| 正文形态 | 摘要/明细分层：摘要 ≤10 行可读清结论与下一步；`📝 描述` ≤100 字；无字面 `\n` |
| 交付物 | 给出 `--content-file` 草案或可执行命令片段 |
| 边界 | 未代替用户执行 `send-message.js`；无 token 时仅交付文案 |

---

## 负例（应判不达标）

- 正文出现占位（随意数字、未发生路径）且未标注「未提供/须核对」
- 完成/阻断/门禁场景整段省略耗时与会话用量且无说明
- 将「大约」「估计」当精确统计写入正文
- 用户要求发群，但仅以「草稿好了」结束且未引导 `send-message.js`（端到端评测时）

---

## 与 eval 的关联

- Skill 侧真发约束：[skills/wework-bot.md](../skills/wework-bot.md)