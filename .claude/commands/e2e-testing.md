调用 `e2e-testing` 技能设计 E2E 测试方案。

```mermaid
graph LR
    A[/e2e-testing] --> B[Parse scenarios]
    B --> C[Determine test type]
    C --> D[Design verification checklist]
    D --> E[Choose selector strategy]
    E --> F[Identify mock dependencies]
    F --> G[Output test scheme]
```

参数: `$ARGUMENTS`

执行要求：
- 测试用例必须仅基于已提供的场景生成；不得添加需求任务中不存在的场景。
- 与 `build-feature` code mode 联用时，输出必须满足 Gate A/B 最低门槛（参见 `skills/build-feature/rules/tester.md`）。
- 场景信息不足以推断断言条件时，输出"前置信息不足，需补充：<缺失内容>"。
- 选择器优先级：`data-testid` > 语义标签 > 文本内容。
