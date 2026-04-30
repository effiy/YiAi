# E2E 测试规范

> 目录结构、data-testid、Mock 与自动化偏好。Gate A/B 准入与证据标准以 [`implement-code-testing.md`](./implement-code-testing.md) 为真源。

---

## 1. 核心约束

| # | 约束 |
|---|------|
| E0-1 | 每个场景有明确验证步骤和预期结果（来自 `05`） |
| E0-2 | 可交互 UI 元素须标记 `data-testid`，格式 `<功能名>-<元素名>` |
| E0-3 | 断言须来自 `05` 预期结果 |
| E0-4 | API mock 通过 hooks/store 层隔离 |
| E0-5 | 测试文件路径：`tests/e2e/<功能名>/` |
| E0-6 | Mock 仅限 `tests/` 目录，生产代码禁止 mock |

---

## 2. 验证方式

| 方式 | 用途 |
|------|------|
| 真实入口 MVP（强制，Gate A） | 主流程最小可用路径 + 证据 |
| 手动浏览器 | 按检查清单操作 + 截图 |
| 代码审查 | data-testid、入口初始化、组件注册 |
| 构建验证 | JS 控制台无错误、组件正常渲染 |
| AI 自动冒烟（强制，Gate B） | 端到端主流程 + 通过/失败证据 |

Playwright 优先用于 Gate B；未安装时须通过可脚本化命令+可复核日志完成等价自动化，不得以手工替代。

---

## 3. 文件结构

```text
tests/e2e/<功能名>/
├── <场景名>-checklist.md    # 验证清单 + 截图
└── fixtures/                 # mock 数据（可选）
```

---

## 4. 禁止事项

- E2E 测试中 import 项目源码
- 只测成功路径不覆盖失败分支
- Mock 数据使用无意义占位符
- 在 `tests/` 外生成测试文件
- 假设 Playwright 可用