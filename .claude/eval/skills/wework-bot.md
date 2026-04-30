# wework-bot 评测示例

真源：`.claude/skills/wework-bot/SKILL.md`、`rules/message-contract.md`；脚本：`.claude/skills/wework-bot/scripts/send-message.js`。

**评测约束**：本页各用户故事与示例对话的**预期落地行为**均为触发一次 **真实企业微信推送**——在具备 `API_X_TOKEN` 与有效 webhook 配置时，须执行 **`send-message.js` 真实调用**（脚本无演练模式，每次运行均请求网关）。不得以「只写了草稿未发送」作为评测结束状态。

---

## 用户故事 A：阶段通知（长流程观测）

**故事**：作为跟进者，希望在 `implement-code` / `generate-document` 执行过程中收到企业微信群通知，且描述里能还原阶段与证据路径。

**示例输入（对话）**

- 「阶段 6 冒烟通过了，先用 message-pusher 写好正文（含证据路径），再按 implement-code 路由 **正式跑 send-message 真发**。」
- 「generate-document 刚开始生成全文档，**推一条开始状态到群里**（send-message 真发）；正文由 agent 写好再通过 `--content` 或 `-f`。」

---

## 用户故事 B：门禁失败 / 阻断

**故事**：作为跟进者，希望在门禁未通过或流程阻断时，群里能看到原因、证据、恢复点和会话度量（用时、用量等可对账）。

**示例输入（对话）**

- 「门禁失败了：先按 message-pusher 对齐事实（摘要段可读清结论与恢复点），再 **真跑 send-message**；🔍 门禁、📎 证据、🧭 恢复点在摘要可见，详细命令序列放明细。」
- 「流程阻断需要人工介入：**调 wework-bot 正式推送**，不要编造 Token 数字；正文里对缺数据写可核对说明。」

---

## 用户故事 C：完成与文档同步数字

**故事**：作为跟进者，希望在流程结束时推送里出现 **真实的** `import-docs` 同步结果（创建/覆盖/失败），而不是占位符。

**示例输入（对话）**

- 「generate-document 收尾：**发一条 wework-bot 完成通知**；`☁️ 文档同步` 必须是刚跑完 import-docs 的真实数字。」

---

## 用户故事 D：写稿核对后再正式推送

**故事**：作为执行者，希望先在对话或草稿文件里核对正文（路由与文案），再 **必须** 向企业微信群发送。

**示例输入（对话）**

- 「正文先在 message-pusher 里对齐描述≤100 字与必含字段，确认后 **再执行 send-message 真发同一份 `-f` 文件**。」

---

## 使用加强（执行门禁）

- 对话出现「发群 / 企微通知 / wework-bot」任一意图时，评测默认要求一次真实发送，不接受“仅草稿未发”收尾。
- `generate-document` / `implement-code` 的完成通知必须校验 `☁️ 文档同步` 来自**本轮刚执行**的 `import-docs` 统计。
- 若发送失败，结果中必须给出可核对失败原因（token / webhook / 网关响应）与恢复动作，不可仅写“稍后重试”。
- 阻断、门禁失败、流程异常中断三类场景均属于强制通知范围，摘要段应直接可读结论与下一步。

---

## 与 Agent 的配合

推送长文案策划可先对齐 `.claude/agents/message-pusher.md`，再调用脚本；详见 [agents/message-pusher.md](../agents/message-pusher.md)。

完成通知里的 **`☁️ 文档同步`** 须与 **刚执行完的 import-docs** 输出一致；脚本侧评测见 [skills/import-docs.md](./import-docs.md)。

---

## CLI 意图示例（供评测「命令是否拼对」）

下列为用户可能交给助手代为执行的意图描述（非唯一措辞）；**预期均以一次真实推送收尾**（见上文评测约束）。

- 「`API_X_TOKEN` 已从环境读，对当前分支 `--agent implement-code` **发一条阶段通知**。」
- 「不要用命令行传 webhook；从 config.json 解析 robot，然后 **执行 send-message 真发**。」
