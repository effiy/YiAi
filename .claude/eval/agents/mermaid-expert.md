# mermaid-expert 评测示例

真源：`.claude/agents/mermaid-expert.md`。

**评测约束**：专注 Mermaid 语法审查与修复，在 generate-document 步骤 4 含图定稿前执行。

---

## 成功判据（可观测）

| 维度 | 预期 |
|------|------|
| 语法正确 | 修复后的 Mermaid 语法符合规范，可正常渲染 |
| 图类型覆盖 | 支持 sequenceDiagram、graph TB、flowchart 等常见类型 |
| 语义审查 | 图的内容与文档描述一致，不只做纯语法检查 |
| 触发时机 | 在 generate-document 步骤 4 含图定稿前调用 |

---

## 负例（应判不达标）

- 仅做拼写检查而不修复 Mermaid 语法错误。
- 修复后仍存在无法渲染的语法问题。
- 图的语义与文档描述矛盾但未指出。
