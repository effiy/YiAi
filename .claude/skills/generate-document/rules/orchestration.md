---
paths:
  - "skills/generate-document/rules/orchestration.md"
  - "docs/*/01_需求文档.md"
  - "docs/*/02_需求任务.md"
  - "docs/*/03_设计文档.md"
  - "docs/*/04_使用文档.md"
  - "docs/*/05_动态检查清单.md"
  - "docs/*/07_项目报告.md"
---

# 编排与阶段契约规范

> 核心原则、中断门槛、错误降级以 `../SKILL.md` 9 条核心原则为准；本文件只承载**阶段状态机**与**阶段专属行为**。Agent 契约见 `agent-contract.md`；日志见 `orchestration-logging.md`。

## 1. 重要约束（P0）

- **本技能只负责文档生成，不修改代码内容**
- **尽可能一次执行到底**：仅触发 SKILL.md 原则 #9 门槛时中断
- **需人工介入时必须 `wework-bot` 推送**：不得口头告知

## 2. 阶段状态机

| 阶段 | 名称 | 目标 | 解锁条件 |
|------|------|------|----------|
| 1 | 解析 + 规范检索 | 解析功能名，调用 `docs-retriever` | 功能名/init 可定位，规范列表已返回 |
| 2 | 上游 Grounding + 影响分析 | 读取上游文档，`doc-impact-analyzer` 影响链闭合（init：扫描项目代码和配置） | 事实-来源映射完整，影响链写入文档 |
| 3 | 专家生成 | `codes-builder` + `doc-architect`（init：推断架构模式） | 模块划分、接口规范确认 |
| 4 | 逐文档生成 + 自检 | 按规范生成文档；三层审查门禁 + `doc-quality-tracker` | 01-05, 07 生成，门禁通过 |
| 5 | 保存 + 知识策展 | 保存文档，`docs-builder` 策展知识 | 文档已保存到 `docs/<功能名>/` |
| 6 | 文档同步与通知 | **先 `import-docs` 再 `wework-bot`**（强制适用所有命令） | import-docs 已记录真实结果，wework-bot 已按模板发送或记录失败 |

## 3. 阻断点

- 功能名无法解析
- 规范检索失败且无法降级
- 影响链未闭环的阻断性依赖
- Agent 调用失败且无备用方案
- 文档 P0 失败且无法自修复

停止时按 SKILL.md 原则 #9 处理：落盘 → 同步 → 通知 → 兜底。

## 4. wework-bot 通知差异

> 强制要求见 SKILL.md 原则 #7/#9。

- **init 成功**：`📋 类型` 填「项目初始化」
- **更新模式**：`🎯 结论` 体现「更新」；`📦 产物` 注明「更新 N / 保持 N」

## 5. Skill / Agent 分派

> Agent 契约详情见 `agent-contract.md`。

| 类型 | 名称 | 用途 |
|------|------|------|
| Skill | `import-docs` / `wework-bot` | 阶段 6 同步与通知 |
| Agent | `docs-retriever` | 阶段 1 规范检索 |
| Agent | `doc-impact-analyzer` | 阶段 2 影响链分析 |
| Agent | `codes-builder` / `doc-architect` | 阶段 3 架构设计 |
| Agent | `doc-mermaid-expert` / `doc-reviewer` / `doc-markdown-tester` / `doc-quality-tracker` | 阶段 4 审查与统计 |
| Agent | `docs-builder` | 阶段 5 知识策展 |

## 6. Agent 调用门禁

> SKILL.md 原则 #4 定义统一要求。本节补充阶段绑定。

- **阶段 1 退出前**：`docs-retriever` 校验通过
- **阶段 2 退出前**：`doc-impact-analyzer` 校验通过
- **阶段 3 退出前**：`doc-architect` 校验通过

未通过不得标记完成、不得进入下一阶段（阻断/降级流程除外）。

校验脚本：
```bash
node skills/implement-code/scripts/validate-agent-output.js --agent <agent名> --text "<输出>"
```

## 7. 编排会话日志

> 详细见 `orchestration-logging.md`。

1. 每次 skill/agent/MCP/memory/shared 交互后立即追加日志
2. 工具：`node scripts/log-orchestration.js`（参数见 `orchestration-logging.md §1.3`）
3. 阻断兜底：对已发生交互仍须补齐日志后再结束