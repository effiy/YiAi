# verification-loop 快速索引

`verification-loop` 对构建、集成、部署等非 UI 场景执行全面验证。核心理念："不依赖重试，依赖准备"。真源在 `SKILL.md`。

## 快速开始

```bash
/verification-loop <验证目标>
```

## 工作流程

1. MCP 可用性探针（禁止静默降级）
2. 阶段 1：环境快照（读取 package.json 等，不执行命令）
3. 阶段 2：静态预检（依赖/类型/import/环境变量/lint）
4. 阶段 3：环境对齐确认
5. 阶段 4：一次执行 + 结果断言

## 使用原则

1. 探针有阻断项禁止进入阶段 1；阶段 1-3 有阻断项禁止进入阶段 4
2. 命令名须取自 `package.json scripts`，不得硬编码
3. 阶段 4 失败不自动重试，给出"一次性修复清单"
4. automation degradation 须标注 ⚠️