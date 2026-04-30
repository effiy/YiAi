# generate-document README

> 行为真源：[SKILL.md](./SKILL.md)；本文件只保留快速开始与命令速查。

## 快速开始

```bash
/generate-document init                           # 项目初始化
/generate-document 用户登录-支持手机号验证码登录    # 功能文档集
/generate-document weekly                         # 本周周报
/generate-document weekly 2026-04-29              # 指定日期周报
/generate-document from-weekly docs/周报/<自然周>/周报.md  # 从周报拆解全文档
```

- 所有命令可反复调用，已存在则增量更新
- 落盘目录：`docs/<功能名>/`，编号集 01-05, 07（06 仅由 `implement-code` 写入）
- 结束时强制：`import-docs`（同步）→ `wework-bot`（通知），中断/完成均不可省略

## 命令速查

| 命令 | 产出 | 首次行为 | 再次行为 | 版本处理 |
|------|------|---------|---------|---------|
| `init` | 10 个基础文件 + `docs/项目初始化/01-07` | 新建 | 更新事实，保留约定 | 头部日期更新 |
| `<功能名>-<描述>` | `docs/<功能名>/01-05,07` | 新建全文档集 | 差异对比，级联更新 | 次版本 `+1` |
| `weekly [日期]` | `docs/周报/<自然周>/周报.md` | 新建 | 同周覆盖更新 | 次版本 `+1` |
| `from-weekly <周报路径>` | 多个 `docs/<功能名>/` 全文档集 | 新建多个目录 | 各目录独立按"已存在则更新" | 各目录独立 `+1` |

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
| 周报 | `docs/周报/<自然周>/周报.md` | ❌ | 单文档，非编号集 |

## 真源与契约

| 来源 | 路径 | 用途 |
|------|------|------|
| 行为真源 | `./SKILL.md` | 核心原则 + 工作流 + 命令 |
| 文档契约 | `../../shared/document-contracts.md` | 文档结构与回写 |
| 影响分析契约 | `../../shared/impact-analysis-contract.md` | 影响链闭合 |
| 证据与反幻觉 | `../../shared/evidence-and-uncertainty.md` | 事实来源约束 |
| Agent 输出契约 | `../../shared/agent-output-contract.md` | 门禁校验 |
| 路径约定 | `../../shared/path-conventions.md` | 目录与命名 |
| Skill/Agent 边界 | `../../shared/agent-skill-boundaries.md` | 职责划分 |

## 目录导航

- `SKILL.md`：唯一真源（9 条核心原则 + 命令 + 工作流入口）
- `rules/`：各文档类型规范 + 编排细则
- `templates/`：可选骨架（03/05 禁用模板）
- `checklists/`：专项检查清单（P0/P1/P2）
- `checklist.md`：检查清单入口索引