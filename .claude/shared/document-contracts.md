# 文档契约总览

本文档定义本仓库文档生成体系中的核心契约，作为 `generate-document` 与相关规则文件的共享解释层。

## 文档类型矩阵

| 类型 | 规范 | 模板 | 单独生成路径 | 全文档路径 | 说明 |
|------|------|------|-------------|-----------|------|
| 需求文档 | `skills/generate-document/rules/需求文档.md` | 可用 | `docs/01_需求文档/` | `docs/<功能名>/01_需求文档.md` | 模板骨架 + 规范约束 |
| 需求任务 | `skills/generate-document/rules/需求任务.md` | 可用 | `docs/02_需求任务/` | `docs/<功能名>/02_需求任务.md` | 模板骨架 + 规范约束 |
| 设计文档 | `skills/generate-document/rules/设计文档.md` | 禁用 | `docs/03_设计文档/` | `docs/<功能名>/03_设计文档.md` | 只读规范与上游事实 |
| 使用文档 | `skills/generate-document/rules/使用文档.md` | 不提供 | `docs/04_使用文档/` | `docs/<功能名>/04_使用文档.md` | 规范驱动 |
| 动态检查清单 | `skills/generate-document/rules/动态检查清单.md` | 禁用 | 仅全文档模式 | `docs/<功能名>/05_动态检查清单.md` | 从上游文档动态抽取 |
| 实施总结 | `implement-code` 技能输出 | 不适用 | 不单独生成 | `docs/<功能名>/06_实施总结.md` | 不由 `generate-document` 生成 |
| 项目报告 | `skills/generate-document/rules/项目报告.md` | 不提供 | `docs/05_项目报告/` | `docs/<功能名>/07_项目报告.md` | 基于真实变更数据 |
| 周报 | `skills/generate-document/rules/周报.md` | 禁用 | `docs/周报/<自然周>/周报.md` | 不适用 | 单文档，不与全文档编号集关联；规范驱动 |
| 通用文档 | `skills/generate-document/rules/通用文档.md` | 可用 | `docs/` | 不适用 | 模板骨架 + 规范约束 |
| 运行/阻断记录 | skill 强制落盘契约 | 不适用 | `docs/99_agent-runs/` | 不适用 | 当无法确定目标文档路径时的兜底记录 |

## 术语定义

- **规范**：强约束，定义章节结构、必填项和禁止事项。
- **模板**：弱约束，只提供起手骨架。
- **检查清单**：验收维度，按 P0 / P1 / P2 划分。
- **全文档**：同一功能在 `docs/<功能名>/` 下的阶段化文档集合。
- **Grounding**：所有技术事实必须能追溯到上游文档或代码。
- **运行/阻断记录**：当 skill 因缺少参数、目标目录不可定位或前置材料缺失而无法写入目标产物时，仍必须写入 `docs/99_agent-runs/` 的 Markdown 记录。
- **全项目影响链分析**：按 `impact-analysis-contract.md` 搜索上游依赖、反向依赖、传递依赖、导出链、注册链、测试、文档、配置与外部依赖影响，作为需求任务、设计文档和代码实施的 P0 前置条件。
- **证据与不确定性**：可采纳、可核对的陈述与待补充的边界，见 `evidence-and-uncertainty.md`；`generate-document` 与 `implement-code` 的正文与总结均须遵守，禁止用叙事代替证据。

## 真源优先级

1. `SKILL.md`
2. `shared/evidence-and-uncertainty.md`（与 `rules` 同遇冲突时，以本矩阵未覆盖的禁止性条款为准，其余以 `SKILL` / `rules` 为准）
3. `rules/*.md`
4. `checklists/*.md`
5. `templates/*.md`
6. `README.md`

若不同文件之间存在冲突，以上述优先级解决，不得反向以模板覆盖规范。
