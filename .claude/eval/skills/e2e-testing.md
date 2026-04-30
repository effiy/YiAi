# e2e-testing 评测示例

真源：`.claude/skills/e2e-testing/SKILL.md`；准入底线真源：`../implement-code/rules/implement-code-testing.md`。

**评测约束**：测试用例只能基于已提供的场景生成，不得自行添加未在需求任务中出现的场景；与 `implement-code` 联用时须满足 Gate A/B。

---

## 成功判据（可观测）

| 维度 | 预期 |
|------|------|
| 测试先行 | 测试方案与验收标准在代码实施前产出；每个实现点均对应已定义的验证步骤 |
| 场景忠实 | 测试用例仅基于已提供的场景，无自行新增场景 |
| 断言完整 | 每个场景给出明确的操作步骤与预期结果断言；信息不足时标注"前置信息不足，需补充：…" |
| 选择器策略 | 优先级声明为 `data-testid` > 语义标签 > 文本内容 |
| Gate A/B | 与 `implement-code` 联用时，产出满足 Gate A（MVP 验证）和 Gate B（冒烟测试）要求 |
| Mock/数据 | 明确列出需 mock 的外部依赖与测试数据构造方式 |

---

## 负例（应判不达标）

- 自行编造未在需求任务中出现的测试场景。
- 场景描述不足时仍编造断言条件而非标注缺失。
- 未声明选择器优先级或默认使用不稳定的文本内容定位。

---

## 与 eval 的关联

- implement-code 测试准入底线：`../implement-code/rules/implement-code-testing.md`
- 需要并行专家角色时，改用 `../../agents/e2e-tester.md` 评测。
