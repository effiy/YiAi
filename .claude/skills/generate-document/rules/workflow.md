---
paths:
  - "docs/*/01_需求文档.md"
  - "docs/*/02_需求任务.md"
  - "docs/*/03_设计文档.md"
  - "docs/*/04_使用文档.md"
  - "docs/*/05_动态检查清单.md"
  - "docs/*/07_项目报告.md"
---

# 功能文档 5 步工作流

> 适用于 `/generate-document <功能名>-<描述>`。`init`/`weekly`/`from-weekly` 差异见 `../SKILL.md`。
> 核心原则、审查门禁以 `../SKILL.md` 为准；阶段状态机见 `orchestration.md`。

## 步骤 1：解析 + 规范检索 + 既有文档探测

- 提取 `{功能名}`
- **探测既有文档**：`docs/{功能名}/` 是否存在有效 Markdown
  - 不存在：新建模式
  - 已存在：加载 01-03 → 对比用户输入 → 识别差异 → 产出更新影响表
- **必须调用 `docs-retriever`**
- 产出：功能名、规范集、上游清单、既有文档状态、更新影响表

## 步骤 2：上游 Grounding + 影响分析

- 按依赖顺序读取 01→02→03；设计文档同时读相关源码
- **必须调用 `doc-impact-analyzer`**（仅02/03）：先读 `../../../shared/impact-analysis-contract.md`
- 影响链写入02第6章/03第5章
- 产出：事实-来源映射表、影响链闭合

## 步骤 3：专家生成

- **必须调用 `codes-builder`**（03生成前）
- **必须调用 `doc-architect`**（03生成前）：5 必答问题须采纳到03架构章节
- 产出：设计方案、模块划分、接口规范

## 步骤 4：逐文档生成 + 自检

### 生成策略

新建：按 `rules/<类型>.md` 章节顺序完整产出。

更新策略：

| 文件 | 更新策略 |
|------|----------|
| 01 | 重写变更章节，未变更保留原文 |
| 02 | 01 变更则同步更新；影响分析必须重新调用 |
| 03 | 01/02 scope 变更则重新调用 codes-builder + doc-architect |
| 04 | 按03最新状态重建 |
| 05 | 从最新02/03重新抽取 |
| 07 | 追加更新记录与验证结论 |

### 三层审查门禁

1. **语法层**：含 Mermaid → `doc-mermaid-expert` 审查写回
2. **质量层**：设计文档 → `doc-reviewer`（P0 修复后才保存）
3. **测试层**：`doc-markdown-tester` 验证链接/代码/术语

### 自检与质量统计

- 加载 `checklists/<类型>.md`，P0 全通过才保存；最多自修复 1 轮
- `doc-quality-tracker` 统计 P0/P1/P2

## 步骤 5：保存 + 知识策展

新建：创建 `docs/<功能名>/`，01-05, 07，版本 `v1.0`。
更新：受影响文件覆盖写入；次版本 `+1`，破坏性变更允许主版本 `+1`。

`docs-builder` 知识策展（更新模式优先追加「更新触发与级联影响」）。

## 步骤 6：文档同步与通知（强制）

> SKILL.md 原则 #7。先 `import-docs`，再 `wework-bot`，禁止颠倒。

### import-docs

`node .claude/skills/import-docs/scripts/import-docs.js --dir docs --exts md`
记录真实结果供 wework-bot 使用。`API_X_TOKEN` 缺失时记录"本轮未执行同步"。

### wework-bot

按 `../wework-bot/SKILL.md` 生动总结格式。必填：`⏱️ 用时` / `🪙 会话用量` / `🤖 模型` / `🧰 工具` / `🕒 最后更新` / `☁️ 文档同步`（已执行时填真实结果）。更新模式：`🎯 结论` 体现「更新」，`📦 产物` 注明「更新 N / 保持 N」。