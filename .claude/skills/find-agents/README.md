# find-agents 快速索引

`find-agents` 在 `.claude/agents/` 下发现并推荐可并行调用的代理。真源在 `SKILL.md`。

## 快速开始

```bash
/find-agents <文档类型> <任务目标>
```

## 常用场景映射

| 场景 | 推荐代理 |
|------|---------|
| 设计文档生成前 | `planner` + `architect` + `impact-analyst` |
| 保存后审查 | `doc-reviewer` + `code-reviewer` |
| 涉及安全鉴权 | `security-reviewer` |
| implement-code 阶段 0 | `spec-retriever` + `docs-lookup` + `architect` |

## 使用原则

1. 只返回 `.claude/agents/` 下真实存在的代理，禁止编造
2. 代理列表默认可同时调用，无顺序依赖
3. 代理仅作候选，最终是否采纳由调用方决定