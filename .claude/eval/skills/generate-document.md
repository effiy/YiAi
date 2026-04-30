# generate-document 评测示例

真源：`.claude/skills/generate-document/SKILL.md`、`rules/orchestration.md`、`rules/*.md`；编排会话日志：`.claude/skills/generate-document/scripts/log-orchestration.js` → **`docs/周报/<YYYY-MM-DD>~<YYYY-MM-DD>/logs.md`**（Markdown）；收尾链路：`import-docs`、`wework-bot`（见 [wework-bot.md](./wework-bot.md)）。

**评测约束**：须对照 SKILL 中的阶段契约：**spec-retriever → impact-analyst → architect / planner → 文档生成（含 Mermaid 时必须先 `mermaid-expert`）与自检 → knowledge-curator → 步骤 6 先 `import-docs` 再 `wework-bot`**；不得以颠倒顺序、未调用必选 Agent、或“仅描述未执行收尾脚本”作为通过状态。涉及 `.claude` 内 skill、agent、MCP、memory/shared 的交互，预期每轮完成后写入 **`docs/logs`**：**操作场景**（与本评测文档「示例输入（对话）」同类句式）+ **对话与交互摘要**（可核对）。

---

## 用户故事 A：全文档编号集交付

**故事**：作为审核者，希望在 `docs/<功能名>/` 下得到 01–05、07 完整文档集，且设计文档 / 动态检查清单为规范驱动、非模板填空。

**示例输入（对话）**

- 「按 generate-document 为「某某功能」生成全文档集；设计文档必须采纳 architect / planner 必答结论。」
- 「生成前先跑 spec-retriever，再按依赖读 01→02→03；影响链写进需求任务第 6 章 / 设计第 5 章。」

---

## 用户故事 B：init 与周报

**故事**：作为维护者，希望在 `init` 或 `weekly` 命令下行为与 SKILL「命令扩展」一致，且收尾仍执行步骤 6（import-docs + wework-bot）。

**示例输入（对话）**

- 「`/generate-document init`：按 SKILL 落盘 10 个基础文件 + `docs/项目初始化/` 01–07，类型通知填项目初始化。」
- 「`/generate-document weekly 2026-04-29`：周报落在 `docs/周报/2026-04-27~2026-05-03/周报.md`（自然周周一至周日），仍要先 import-docs 再企微通知。」

---

## 用户故事 C：阻断与兜底记录

**故事**：作为跟进者，希望在无法解析功能名或前置阻断时，有明确的 `docs/99_agent-runs/` 或编排约定中的兜底路径，且阻断通知仍含必填字段。

**示例输入（对话）**

- 「功能名解析失败：先写 `docs/99_agent-runs/` 记录再提示用户；阻断也要 wework-bot。」

---

## 用户故事 D：从周报拆解多套全文档（from-weekly）

**故事**：作为维护者，希望指定一份已有周报，将其「四、后期规划与改进优先级总表」中的条目梳理为需求，并生成多个 `docs/<功能名>/` 全文档集；全部完成后只做一次 import-docs 与一条汇总企微通知。

**示例输入（对话）**

- 「`/generate-document from-weekly docs/周报/2026-04-27~2026-05-03/周报.md`：按表格行拆功能目录，并写 `docs/99_agent-runs/*_from-weekly.md` 映射表。」
- 「优先处理类型为规划与项目的行；系统类单独成 `系统改进-…` 目录。」

---

## 编排会话日志（可观测）

评测时可抽查当周 `docs/周报/<自然周>/logs.md`：是否存在与 **skill/agent/MCP** 交互对应的 Markdown 小节（三级标题内含 ISO 时间与 kind/name），且 **对话与交互摘要** 非空、可与本会话的用法对齐。可选抽查 **`--case good|bad`** 与 **`docs/logs/CASE-STANDARD.md`** 是否一致（分级、标签、后续改进是否支撑复盘）。

---

## 与 eval 的关联

- 文档导入脚本评测：[import-docs.md](./import-docs.md)
- 企微真发与 import-docs 顺序：[wework-bot.md](./wework-bot.md)
- 写稿 agent：[message-pusher.md](../agents/message-pusher.md)
- 实施代码编排对照：[implement-code.md](./implement-code.md)
