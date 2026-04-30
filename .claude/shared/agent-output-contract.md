# Agent 输出契约（可校验附录）

本文件为 `generate-document` / `implement-code` 在调用专家 agent 时提供**机器可校验**的输出附录约定，用于将“必答问题覆盖”“关键字段齐全”等要求从软约束变成可执行门禁。

## 1. 适用范围

- `agents/spec-retriever.md`
- `agents/impact-analyst.md`
- `agents/architect.md`
- `agents/code-reviewer.md`
- `agents/mermaid-expert.md`
- `agents/planner.md`
- `agents/quality-tracker.md`
- `agents/knowledge-curator.md`
- `agents/docs-lookup.md`

若其他 agent 也要纳入门禁，可按本文件扩展。

> **注**：`quality-tracker`、`knowledge-curator`、`docs-lookup` 无特定必答问题，其 `required_answers` 字段允许为空数组 `[]`，但 `artifacts` 字段仍须标明关键产物存在性。

## 2. 输出必须包含 JSON 附录块（强制）

每个 agent 的输出在末尾**必须**附加一个 JSON fenced code block，形如：

```json
{
  "agent": "spec-retriever",
  "contract_version": "1.0",
  "task": {
    "skill": "generate-document",
    "stage": "stage-1",
    "doc_type": "需求文档",
    "feature": "Foo-条目筛选"
  },
  "required_answers": [
    { "id": "Q1", "answered": true, "evidence": ["skills/generate-document/rules/需求文档.md"] }
  ],
  "artifacts": {
    "required_specs": ["skills/generate-document/rules/通用文档.md"],
    "optional_specs": []
  },
  "warnings": [],
  "notes": "一行摘要"
}
```

### 字段要求

- **agent**：必须等于该 agent 的 `name`（如 `spec-retriever`）。
- **contract_version**：当前固定为 `"1.0"`。
- **task.skill**：`generate-document` 或 `implement-code`。
- **task.stage**：对 `generate-document` 以 `stage-1..stage-6` 标识；对 `implement-code` 以其规则定义的阶段标识。
- **task.doc_type**：本次调用聚焦的文档类型；不适用时可填 `"N/A"`。
- **required_answers**：必须覆盖该 agent 定义的“必答问题”全集；每项的 `answered` 必须为 `true`，否则视为契约未满足。
- **artifacts**：把 agent 的关键产物结构化出来（例如：规范列表、影响分析四表、架构图等的“存在性”）。
- **warnings**：非阻断但需显式提示主流程的风险项。
- **notes**：一行摘要，便于日志与通知引用。

## 3. 门禁规则（调用方必须执行）

调用方（通常是 `skills/generate-document` 编排）在采纳 agent 结论前必须执行：

1. **校验 JSON 附录存在且可解析**
2. **校验 `agent` 与被调用 agent 一致**
3. **校验 `required_answers` 全部 `answered=true`**
4. **按 agent 类型校验产物字段存在性**

失败时的处理策略：

- **第一次失败**：原地追加补问（只要求补齐缺失字段/问题，不要重写全部内容）
- **第二次失败**：视为 agent 调用失败，进入 skill 的阻断/降级策略（记录证据、通知、恢复点）

## 4. 本仓库提供的校验脚本

仓库内提供 `skills/implement-code/scripts/validate-agent-output.js` 用于对上述 JSON 附录做快速门禁校验：

```bash
node skills/implement-code/scripts/validate-agent-output.js --agent spec-retriever --file /path/to/output.txt
```

该脚本只校验“契约结构与必答问题覆盖”，不校验内容真伪；真伪仍由 `shared/evidence-and-uncertainty.md` 与上游证据链约束。

