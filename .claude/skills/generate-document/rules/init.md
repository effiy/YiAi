---
paths:
  - "CLAUDE.md"
  - "README.md"
  - "docs/architecture.md"
  - "docs/changelog.md"
  - "docs/devops.md"
  - "docs/network.md"
  - "docs/state-management.md"
  - "docs/FAQ.md"
  - "docs/auth.md"
  - "docs/security.md"
  - "docs/项目初始化/**/*.md"
---

# 项目初始化（init）命令规范

> 核心原则、中断门槛、通知要求以 `../SKILL.md` 为准；本文件只承载 init 专属行为细节。

## 调用方式

```bash
/generate-document init
```

## 产出清单

| 类别 | 产出 | 说明 |
|------|------|------|
| 项目基础文件（10 个） | `CLAUDE.md`、`README.md`、`docs/architecture.md` 等 | 仓库根目录或 `docs/` |
| 全文档编号集（7 个） | `docs/项目初始化/01-07` | 含 `06_实施总结.md`（由 init 自行写入） |

## 工作流

1. 扫描仓库结构：读取 `package.json` / 构建配置 / 源码目录 / git 历史等
2. 阶段 1：调用 `docs-retriever` 检索适用规范
3. 阶段 2：扫描项目代码和配置（init 无影响分析需求，跳过 `doc-impact-analyzer`）
4. 阶段 3：调用 `codes-builder` + `doc-architect` 推断项目架构模式
5. 阶段 4：生成 10 个基础文件 + `docs/项目初始化/` 01-07；三层审查门禁 + `doc-quality-tracker` 统计
6. 阶段 5：保存文档，调用 `docs-builder` 策展知识
7. 阶段 6：先 `import-docs`，再 `wework-bot`

## 再次执行（re-init）更新策略

| 策略 | 说明 |
|------|------|
| 优先更新事实 | 技术栈、目录结构、命令、入口等必须刷新 |
| 保留人工补充 | 团队约定/经验沉淀若已存在且未与事实冲突，默认保留 |
| 冲突标注 | 陈述与代码事实冲突时标注 `> 待确认（原因：…）` |
| 哨兵块安全重写 | `<!-- AUTO-GENERATED:BEGIN/END -->` 包裹的段落可重写，保留块外内容 |
| 可观测更新 | 在 `06_实施总结.md` 记录本轮更新摘要 |

## init 与功能文档的区别

| 维度 | `init` | `<功能名>-描述` |
|------|--------|----------------|
| 功能名 | 固定为 `项目初始化` | 用户指定 |
| 06_实施总结 | 由 init 自行写入 | 由 implement-code 写入 |
| 产出位置 | 根目录 10 个文件 + `docs/项目初始化/` | `docs/<功能名>/` |
| 更新策略 | re-init：刷新事实、保留约定、冲突标待确认 | 差异对比、级联更新、版本递增 |