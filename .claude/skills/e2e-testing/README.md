# e2e-testing 快速索引

`e2e-testing` 将 UI 用户流程场景转化为可执行的 E2E 测试方案。真源在 `SKILL.md`。

## 快速开始

```bash
/e2e-testing <场景描述文件或需求任务路径>
```

## 使用原则

1. 测试用例只能基于已提供的场景生成，不得自行添加
2. 场景不足以推断断言条件时，输出"前置信息不足，需补充：…"
3. 与 `implement-code` 联用时，准入底线以 `../implement-code/rules/implement-code-testing.md` 为准
4. 若需要并行专家角色或必答问题，改用 `../../agents/e2e-tester.md`