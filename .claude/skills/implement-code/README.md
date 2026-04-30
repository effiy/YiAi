# implement-code 快速索引

## 阅读顺序

1. [`SKILL.md`](./SKILL.md) — 适用条件、4 阶段总览、门禁与停止条件
2. [`rules/orchestration.md`](./rules/orchestration.md) — 阶段契约、文档 Grounding、§3.4 覆盖预检、skill/agent 分派
3. [`rules/implement-code-testing.md`](./rules/implement-code-testing.md) — Gate A/B 定义与证据标准
4. 按阶段进入规则文件：
   - 阶段 1：`implement-code-testing` + `e2e-testing` + `test-page`
   - 阶段 2/6：`verification-gate`
   - 阶段 3/4：`code-implementation`
   - 阶段 7/阻断：`process-summary`
5. [`rules/artifact-contracts.md`](./rules/artifact-contracts.md) — 产物路径与回写约定
6. [`../../shared/impact-analysis-contract.md`](../../shared/impact-analysis-contract.md) — 影响链分析范围与 P0 门禁

## 真源分工

| 文件 | 职责 |
|------|------|
| `SKILL.md` | 主编排器 |
| `rules/orchestration.md` | 阶段契约与编排细则 |
| `rules/artifact-contracts.md` | 产物路径、命名、回写 |
| `rules/implement-code-testing.md` | Gate A/B 准入与证据（真源） |
| `rules/verification-gate.md` | 门禁原则、修复循环、最终闭环 |
| `rules/code-implementation.md` | 编码约束与自检 |
| `rules/process-summary.md` | 总结文档结构 |
| `rules/e2e-testing.md` | E2E 目录与 data-testid |
| `rules/test-page.md` | 原型页面规范 |