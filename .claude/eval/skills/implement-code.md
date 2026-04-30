# implement-code 评测示例

真源：`.claude/skills/implement-code/SKILL.md`、`rules/orchestration.md`、`rules/code-implementation.md` 等；编排会话日志：`.claude/skills/generate-document/scripts/log-orchestration.js` → **`docs/周报/<YYYY-MM-DD>~<YYYY-MM-DD>/logs.md`**（Markdown）；收尾：**先 `import-docs` 再 `wework-bot`**（见 [wework-bot.md](./wework-bot.md)）。

**评测约束**：须对照 SKILL：**若为 git 仓库，全过程必须在 `feat/<功能名>` 上实施（与 `{功能名}` 一致），首个改动前完成分支就绪**（见 `rules/orchestration.md` §2.5）；P0 文档不齐须阻断并生成阻断版总结；阶段内必选 **spec-retriever、impact-analyst、architect** 及代码阶段的 **code-reviewer** 等契约；结束必须 **import-docs + wework-bot** 两步齐备，且不得以“只产生命令/草稿未真实执行”作为通过状态。涉及 `.claude` 内 skill、agent、MCP、memory/shared 的交互，预期每轮完成后写入 **`docs/logs`**：**操作场景** + **对话与交互摘要**（格式见 SKILL「编排会话日志」）。

---

## 用户故事 A：文档驱动实施

**故事**：作为审核者，希望代码变更可回溯到 `docs/<功能名>/` 下 02、03、05，且影响链分析与架构确认在实施前已完成。

**示例输入（对话）**

- 「`/implement-code 某某功能`：先预检 P0 文档，再 impact-analyst 全链闭合，architect 对齐架构约定。」
- 「每模块完成后跑 code-reviewer，P0 必须修。」

---

## 用户故事 B：list 与分支

**故事**：作为使用者，希望 `/implement-code list` 能列举 `docs/` 下功能目录；进入实施时**必须**在 **`feat/<功能名>`** 上工作（与所选功能同名），不得在错误分支改代码。

**示例输入（对话）**

- 「先 list 看有哪些功能文档再选一个 implement-code。」
- 「先 `git switch -c feat/<功能名>` 或切换到已有 `feat/<功能名>`，再动任何代码。」

---

## 用户故事 C：阻断与门禁异常

**故事**：作为跟进者，希望在 P0 缺失、审查不可修复或门禁失效时，有阻断版 `06_实施总结.md`、文档状态回写与 **import-docs + wework-bot**（阻断 / 门禁异常模板）。

**示例输入（对话）**

- 「P0 文档缺一份：应停止并生成阻断总结，再发企微阻断通知。」
- 「wework-bot 失败时：失败摘要须写回 `06` 或 `docs/99_agent-runs/`。」

---

## 用户故事 D：测试前置与自动冒烟

**故事**：作为交付负责人，希望 implement-code 严格执行「先测后写、写后自动冒烟」：**写代码前（Gate A）**在真实入口完成主路径最小可用验证并留可追溯证据；**写代码后（Gate B）**由 AI 自动跑通主流程冒烟并留可复核产物。任一步缺失须阻断，不得进入下一阶段或交付总结。

**验收要点（评测时可对照）**

- 真源为 `.claude/skills/implement-code/rules/implement-code-testing.md`；`e2e-testing.md` 仅承载 UI 目录与 testid 等格式。
- Gate A：证据至少包含命令行、退出码、日志路径、`tests/` 下 checklist 或截图路径之一；禁止仅凭口述「试过」。
- Gate B：须由 AI **实际执行**自动化或可脚本化链路（Playwright 优先）；不得以「请你本地手动点点」代替通过判定。
- P0 动态检查项须与 Gate B 对齐；`verification-gate.md` §7–§9 与最终 `05` 回写序列（§9.3）满足后方可宣称实施完成。

**示例输入（对话）**

- 「开始编码前，先在真实入口把主流程最小可用链路跑通并留证据。」
- 「代码完成后，用 AI 自动全流程跑主路径冒烟，没通过不能进入总结与通知。」
- 「对照 implement-code-testing Gate A/B，检查 06 里有没有证据路径。」

---

## 编排会话日志（可观测）

评测时可抽查当周 `docs/周报/<自然周>/logs.md`：是否存在与 **skill/agent/MCP** 交互对应的 Markdown 小节，且 **对话与交互摘要** 含可核对要点；可选对照 **`docs/logs/CASE-STANDARD.md`** 检查 `--case` / `--tags` / `--lesson` 用法。

---

## 与 eval 的关联

- 文档导入脚本评测：[import-docs.md](./import-docs.md)
- 企微真发与文档同步：[wework-bot.md](./wework-bot.md)
- 文档生成编排对照：[generate-document.md](./generate-document.md)
- 写稿 agent：[message-pusher.md](../agents/message-pusher.md)
