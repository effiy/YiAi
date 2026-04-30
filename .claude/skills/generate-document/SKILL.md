---
name: generate-document
description: |
  文档生成编排器。在 `docs/<功能名>/` 下创建或更新全文档编号集（01-05, 07），5 步工作流驱动，三层审查门禁把关。
  结束时强制执行 `import-docs`（文档同步）→ `wework-bot`（群通知），中断/完成均不可省略。
  支持：`/generate-document 功能名-描述`（功能文档）、`init`（项目初始化）、`weekly`（周报）、`from-weekly <周报路径>`（从周报拆解全文档）。
---

# generate-document

> 命令速查见 [README.md](./README.md#命令速查)

## 核心原则

1. **只生成文档，不改代码** — 绝对不修改任何代码文件
2. **规范驱动，防幻觉** — `rules/<类型>.md` 是唯一契约；`03_设计文档` 和 `05_动态检查清单` 禁用模板。技术事实必须可追溯到上游文档或代码；无据可依时写 `> 待补充（原因：…）`，禁止虚构
3. **Agent 实干，必答必采纳** — 关键步骤必须调用 agent，必须采纳其必答问题。调用链路见 [agent-contract.md](./rules/agent-contract.md)
4. **审查门禁（三层递进）** — 语法层（Mermaid）→ 质量层（设计文档）→ 测试层（Markdown 质量）。契约校验见 [agent-contract.md §4](./rules/agent-contract.md#4-门禁校验)
5. **全文档交付，级联刷新** — 编号集 01-05, 07；级联规则：01 变更 → 02/03 重写，02/03 变更 → 04/05 重写，07 追加更新
6. **测试先行** — `02_需求任务.md` 每个场景须有可验证的验收标准；`05_动态检查清单.md` 须含可执行 P0 检查项
7. **中断与完成必须通知** — 流程结束必须先 `import-docs` 再 `wework-bot`，不得省略、颠倒或静默降级
8. **自检闭环** — P0 全部通过才保存为通过状态；最多自修复 1 轮；仍不通过也必须保存，顶部标注未通过项
9. **一次执行到底** — 默认不中断，缺失信息写"待确认"继续推进；仅命中阻断门槛才打断，打断后按原则 #7 收尾

### 阻断门槛与降级

> 详细降级策略见 [orchestration.md](./rules/orchestration.md#4-阻断点)

| # | 场景 | 能否降级 |
|---|------|----------|
| H1 | 功能名无法解析且无法生成合理默认 | 否 |
| H2 | P0 章节缺上游来源，且无法"待补充"降级 | 否 |
| H3 | 同一请求指向两个不兼容的功能域 | 否 |
| H4 | `from-weekly`：周报无效或无可落地条目 | 否 |
| H5 | `API_X_TOKEN` 缺失 | 是（跳过同步，通知照发） |

打断后统一 4 步：落盘 → 同步（H5 跳过）→ 通知 → 兜底

---

## 全文档类型一览

| 类型 | 文件名 | 模板 | 生成方式 |
|------|--------|------|----------|
| 需求文档 | `01_需求文档.md` | ✅ | 模板骨架 + 规范约束 |
| 需求任务 | `02_需求任务.md` | ✅ | 模板骨架 + 规范约束 |
| 设计文档 | `03_设计文档.md` | ❌ | **仅规范驱动** |
| 使用文档 | `04_使用文档.md` | ❌ | 规范驱动 |
| 动态检查清单 | `05_动态检查清单.md` | ❌ | **仅规范驱动** |
| 实施总结 | `06_实施总结.md` | — | **仅 implement-code 写入** |
| 项目报告 | `07_项目报告.md` | ❌ | 规范驱动 + 真实变更数据 |

---

## 5 步工作流

> 详细步骤见 [workflow.md](./rules/workflow.md)

示例：`/generate-document 用户登录-支持手机号验证码登录`

---

## 命令：项目初始化（init）

> 详细规范见 [init.md](./rules/init.md)

示例：`/generate-document init`

---

## 命令：周报（weekly）

> 详细规范见 [weekly.md](./rules/weekly.md)

示例：`/generate-document weekly` 或 `/generate-document weekly 2026-04-29`

---

## 命令：从周报拆解全文档（from-weekly）

> 详细规范见 [from-weekly.md](./rules/from-weekly.md)

示例：`/generate-document from-weekly docs/周报/2026-04-27~2026-05-03/周报.md`

---

## Agent 调用契约

> 详细规范见 [agent-contract.md](./rules/agent-contract.md)

---

## 编排会话日志（强制）

> 详细规范见 [orchestration-logging.md](./rules/orchestration-logging.md)

---

## 支持文件结构

```
.claude/skills/generate-document/
├── SKILL.md                 # 入口 + 9 条核心原则 + 命令说明（唯一真源）
├── README.md                # 快速开始 + 命令速查 + 真源索引
├── checklist.md             # 检查清单入口索引
├── checklists/              # 各文档类型检查清单
├── rules/                   # 各文档类型规范 + 编排细则
│   ├── workflow.md          # 5 步工作流
│   ├── orchestration.md     # 阶段状态机 + 阻断降级
│   ├── agent-contract.md    # Agent 调用契约
│   ├── orchestration-logging.md # 编排会话日志
│   ├── init.md / weekly.md / from-weekly.md  # 命令规范
│   ├── 需求文档.md / 需求任务.md / 设计文档.md  # 文档类型规范
│   ├── 使用文档.md / 动态检查清单.md / 项目报告.md
│   ├── 项目基础文件.md / 周报.md / 通用文档.md
│   ├── 编码规范.md / 代码结构.md
│   └── ...
└── templates/               # 模板（03/05 禁用）
```
