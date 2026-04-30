调用 `e2e-testing` 技能设计 E2E 测试方案。

参数：`$ARGUMENTS`

执行要求：
- 测试用例只能基于已提供的场景生成，不得自行添加未在需求任务中出现的场景
- 与 `implement-code` 联用时，产出须满足 Gate A/B 准入底线（以 `../implement-code/rules/implement-code-testing.md` 为准）
- 场景不足以推断断言条件时，须输出"前置信息不足，需补充：<缺失>"
- 选择器优先级：`data-testid` > 语义标签 > 文本内容