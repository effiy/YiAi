# code-reviewer 评测示例

真源：`.claude/agents/code-reviewer.md`。

**评测约束**：与 `code-review` skill 的分工须符合 `shared/agent-skill-boundaries.md`；code-reviewer 负责并行专家角色与必答问题，skill 负责审查方法与输出格式。

---

## 成功判据（可观测）

| 维度 | 预期 |
|------|------|
| 必答问题 | 回答所有被调用时要求的必答问题 |
| 专业性 | 输出比 skill 更深入的专家视角（如特定框架最佳实践） |
| 并行性 | 作为并行代理组合中的一员，不隐含顺序依赖 |
| 边界 | 不替代 skill 做格式输出，而是提供深度分析输入 |

---

## 负例（应判不达标）

- 混淆 Skill 与 Agent 职责，直接输出 skill 的分级格式而不提供专家深度分析。
- 未回答必答问题即结束。
