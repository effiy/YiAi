---
name: find-agents
description: 根据文档类型和任务目标在 .claude/agents/ 目录下发现并推荐可并行调用的代理。当需要为文档生成、审查、验证等任务分派专家代理时使用。
---

# find-agents

## 用途

在当前项目的 `.claude/agents/` 目录中发现可用代理，按任务类型推荐并行代理组合及每个代理的"必答问题"。

目录约定和真源说明见 `../../README.md`；若调用方需要区分 Skill 与 Agent 职责，参考 `../../shared/agent-skill-boundaries.md`。

## 输入

- **文档类型**：如 `设计文档`、`项目报告`、`动态检查清单`（必填）
- **任务目标**：如 `生成设计文档`、`审查刚生成的设计文档`（必填）
- **上游上下文摘要**：上游文档路径 + 关键事实 3-5 条（可选）

## 工作步骤

1. 列出 `.claude/agents/` **根目录**下所有 `.md` 文件
2. 读取每个文件的 frontmatter `role` 与 `triggers` 字段
3. 按文档类型与任务目标匹配，选出可并行的代理组合
4. 为每个代理生成"必答问题"

## 默认代理映射

| 触发场景                                                                        | 推荐代理                                                             |
| ------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| 设计文档生成前                                                                  | `planner` + `architect` + `impact-analyst`                           |
| 项目报告生成前                                                                  | `code-reviewer` + `docs-lookup`                                      |
| 动态检查清单 E2E 场景                                                           | `e2e-tester`                                                         |
| 保存后审查                                                                      | `doc-reviewer` + `code-reviewer` + `doc-updater`                     |
| Grounding / 上游定位                                                            | `docs-lookup`                                                        |
| 涉及安全鉴权                                                                    | `security-reviewer`                                                  |
| 规范检索                                                                        | `spec-retriever`                                                     |
| 全项目影响分析                                                                  | `impact-analyst`                                                     |
| 质量趋势追踪                                                                    | `quality-tracker`                                                    |
| 知识策展                                                                        | `knowledge-curator`                                                  |
| 编写企业微信推送文案、补全会话用量与反幻觉核对                                  | `message-pusher`                                                     |
| Markdown 中含 Mermaid 图的语法审查与修复（generate-document 步骤 4 含图定稿前） | `mermaid-expert`                                                     |
| implement-code 阶段 0                                                           | `spec-retriever` + `docs-lookup` + `architect` + `security-reviewer` |
| implement-code 阶段 3/4                                                         | `impact-analyst`                                                     |
| implement-code 阶段 7                                                           | `impl-reporter` + `quality-tracker` + `knowledge-curator`            |

## 输出格式

```
可并行调用的代理：
- <代理名>
  角色：<一句话>
  输入：<需要提供什么>
  输出：<期望返回什么>
  必答问题：
    1. <问题1>
    2. <问题2>
```

## 使用规则

- **禁止编造**：只返回 `.claude/agents/` 下真实存在的代理文件名（不含 `.md`）。
- **并行优先**：返回的代理列表默认设计为可同时调用，不得隐含顺序依赖。
- **代理返回仅作候选**：最终是否写入文档由调用方（如 generate-document）依据规范决定。
