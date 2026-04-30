---
name: implement-code
description: 基于 `docs/<功能名>/` 文档集实施代码，4 阶段推进：预检→实施→验证→总结。结束时强制执行"文档同步 + 群通知"（先 `import-docs`，再 `wework-bot`）。
user_invocable: true
---

# implement-code

## 强制约束

1. **Git 分支**：仓库为 git 时，全过程**只能**在 **`feat/<功能名>`** 上进行（与 `docs/<功能名>/` 一致）。任何代码变更前须检出或新建该分支。禁止在 `main`/`master` 或无关分支上实施。非 git 仓库不适用。
2. **Gate A（测试先行）**：写代码前必须先基于 `02_需求任务.md` 主场景产出可落地的测试方案与验收标准，在真实入口完成 MVP 流程验证并留存证据。细则：[`rules/implement-code-testing.md`](./rules/implement-code-testing.md) §2。
3. **Gate B（冒烟必过）**：代码完成后必须由 AI 自动执行主流程全链路冒烟测试，通过后方可进入总结。细则：[`rules/implement-code-testing.md`](./rules/implement-code-testing.md) §3。
4. **结束必须同步+通知**：先 `import-docs` 同步文档，再 `wework-bot` 发送完成/阻断/门禁异常通知。两步缺一不可。
5. **一次执行到底**：默认按 `rules/` 与项目约定直接推进，不频繁追问；缺失信息写"待确认"并继续。
6. **人工介入必须通知**：阻断/门禁异常/需人工介入时必须发送 wework-bot 通知。

## 定位

`implement-code` 是代码实施编排器：预检文档并完成影响分析 → 按架构实施代码 → 审查验证代码质量 → 生成实施总结。阶段细则由 `rules/` 承载，项目适配由 `rules/code-implementation.md` 承载。

## 核心原则

1. **文档驱动**：实施决策必须能回溯到文档或代码来源
2. **Agent 实干**：关键阶段必须调用 agent 并采纳其必答问题回答
3. **项目适配**：实施顺序和约束按 `rules/code-implementation.md`
4. **影响链闭合**：代码变更前后必须做全项目影响分析
5. **默认自动决策**：尽量不打断，缺失信息写"待确认"并继续
6. **中断与完成必须通知**：先 `import-docs` 同步文档，再 `wework-bot` 发送通知

## 何时使用 / 不使用

- **使用**：已有 `docs/<功能名>/` 文档集 + 用户明确要求实施代码 + 需要按阶段推进
- **不使用**：缺少 P0 文档（02+03+05）/ 用户仍在做需求澄清 / 只是零碎代码修补

## list 命令

`/implement-code list` — 列举 `docs/` 下可用功能目录（排除 `99_agent-runs`）。空结果时建议先运行 `generate-document`。

## 输入前提

P0 文档（缺失即阻断）：`02_需求任务.md`（用户故事/场景/前置条件）、`03_设计文档.md`（模块/接口/约束）、`05_动态检查清单.md`（待验证检查项）

P1/P2 文档（缺失不阻断）：`01_需求文档.md`（背景与目标）、`04_使用文档.md`（UI 文案补充）

## 4 阶段工作流

### 阶段 1：预检 + 影响分析

- 解析 `{功能名}`；git 仓库先就绪 `feat/<功能名>` 分支，再预检 P0 文档
- **必须调用** `spec-retriever`（检索规范）→ `impact-analyst`（全项目影响链闭合分析，结果必须采纳）→ `architect`（架构确认）
- 退出：P0 文档齐全 + 影响链闭合 + 架构确认

### 阶段 2：代码实施

- 进入前必须通过 Gate A（见 `rules/implement-code-testing.md`）
- 按 `rules/code-implementation.md` 逐模块编码
- 每模块完成后调用 `code-reviewer`（P0 立即修复，P1/P2 记录不阻断）
- 每模块自检：P0 语法消除 + 架构约束确认 + data-testid 覆盖 + 影响链回归
- 退出：所有模块实现完成 + 逐模块验证记录齐全

### 阶段 3：验证 + 审查

- 调用 `code-reviewer` 全量审查
- 执行 Gate B（AI 自动主流程冒烟），失败不得进入阶段 4
- 验证 P0 检查项（来自 `05_动态检查清单`）
- 退出：无 P0 审查问题 + P0 检查项全部通过

### 阶段 4：总结 + 交付

- 生成 `06_实施总结.md`（结构见 `rules/process-summary.md`）
- 回写 `01/02/03/04/05/07` 的实施状态
- 调用 `quality-tracker`（统计 P0/P1/P2）→ `knowledge-curator`（提取可复用知识）
- 执行 `import-docs` + `wework-bot`（通知含用时/会话用量/模型/工具/最后更新时间）
- 退出：总结写入完成 + 状态回写完成 + 通知发送完成

## Agent 调用契约

| Agent | 触发阶段 | 采纳规则 |
|-------|---------|---------|
| `spec-retriever` | 1 | 返回规范列表用于后续步骤 |
| `impact-analyst` | 1 | 影响链分析结果必须采纳 |
| `architect` | 1 | 架构方案必须与项目约定一致 |
| `code-reviewer` | 2（每模块）+ 3（全量） | P0 必须修复；P1/P2 记录不阻断 |
| 项目特有 agent | 3 | P0 必须修复 |
| `quality-tracker` | 4 | 统计追加到记忆文件 |
| `knowledge-curator` | 4 | 知识提取到记忆文件 |

## 停止条件

以下情况必须停止并生成阻断版 `06_实施总结.md`：P0 文档缺失 / 影响链未闭环 / 代码审查 P0 无法修复 / 所有模块阻断

停止时：记录阻断原因和产物 → 生成阻断版总结 → 回写阻断状态 → 执行 `import-docs` + `wework-bot` 阻断通知

## 编排会话日志（强制）

每完成一轮 skill/agent/MCP 交互后，追加写入 `docs/周报/<YYYY-MM-DD>~<YYYY-MM-DD>/logs.md`：

```bash
node .claude/skills/generate-document/scripts/log-orchestration.js --skill implement-code \
  --kind <skill|agent|mcp|shared|other> [--name <标识>] \
  [--scenario "<操作场景>"] \
  [--case <good|bad|neutral>] [--tags "<tag1,tag2>"] [--lesson "<后续改进>"] \
  [--text "<单行摘要>"]
```

细则见 `rules/orchestration.md` §6。

## 支持文件结构

```
.claude/skills/implement-code/
├── SKILL.md
├── README.md
└── rules/
    ├── orchestration.md          # 阶段契约与编排细则
    ├── code-implementation.md   # 项目专项约束（已定制）
    ├── artifact-contracts.md    # 产物与回写契约
    ├── verification-gate.md     # 验证规则
    ├── implement-code-testing.md # Gate A/B 准入与证据（真源）
    ├── e2e-testing.md           # E2E 目录与 testid 细则
    ├── process-summary.md       # 总结文档结构
    └── test-page.md             # 原型页规范
```
