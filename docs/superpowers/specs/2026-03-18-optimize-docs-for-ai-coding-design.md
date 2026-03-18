# 优化 docs 目录以适应 AI 编码 - 设计文档

**日期**: 2026-03-18
**项目**: YiAi
**状态**: 待审核

---

## 概述

本设计文档描述了如何优化 YiAi 项目的 `docs/` 目录，使其更适合 AI 编码助手（如 Claude Code）理解和使用，同时保持对人类开发者的友好性。

## 目标

1. **更好的 AI 理解** - 帮助 AI 编码助手更快、更准确地理解项目
2. **更清晰的结构** - 重组文件以实现更好的导航和逻辑分组
3. **结构化约定** - 清晰的命名、一致的模式和明确的组织
4. **快速参考** - 简洁的摘要、速查表和查找表
5. **机器可读** - 格式良好的 Markdown、YAML 等，便于 AI 解析

## 设计方案：方案 1 - 结构化增强 + AI 友好化

### 核心原则

- **非破坏性** - 不删除、不重命名任何现有文件
- **增量式** - 只添加新文件，不修改现有内容
- **双重优化** - 同时优化机器可读性和结构化导航

### 最终目录结构

```
docs/
├── (现有所有文件保持不变...)
│   ├── README.md
│   ├── 架构设计.md
│   ├── API端点.md
│   ├── 数据库集合.md
│   ├── 配置指南.md
│   ├── 核心功能/
│   └── 开发规范/
│
├── INDEX.md                    (新增：结构化总索引)
├── SUMMARY.md                  (新增：GitBook 风格摘要)
│
└── .context/                   (新增：AI 专用上下文目录)
    ├── project-overview.json   (机器可读的项目概览)
    ├── file-patterns.md        (关键文件速查表)
    ├── architecture-map.md     (架构映射与依赖)
    └── code-patterns.md        (编码模式与约定)
```

### 1. INDEX.md - 结构化总索引

**目的**: 提供所有文档的单一树状索引，便于快速导航。

**内容结构**:
- 快速导航（主页、架构、API、数据库、配置）
- 核心功能文档列表
- 开发规范列表
- AI 专用上下文链接

### 2. SUMMARY.md - GitBook 风格摘要

**目的**: 提供 GitBook 兼容的摘要，支持各种文档工具，也便于 AI 解析。

**内容结构**:
- 嵌套列表格式的完整文档树
- 包含所有现有文档和新增文件

### 3. .context/ 目录 - AI 专用上下文

#### 3.1 project-overview.json

**目的**: 提供机器可读的结构化项目概览。

**内容**:
```json
{
  "name": "YiAi",
  "description": "基于 FastAPI 的 AI 服务后端",
  "stack": ["Python", "FastAPI", "MongoDB", "Motor"],
  "entryPoints": ["main.py", "src/main.py"],
  "keyPatterns": {
    "apiRoutes": "src/api/routes/*.py",
    "services": "src/services/*/",
    "core": "src/core/*.py",
    "models": "src/models/*.py"
  }
}
```

#### 3.2 file-patterns.md

**目的**: 关键文件路径和用途速查表。

**内容**:
- 入口点表格
- API 路由表格
- 核心服务表格
- 数据库集合列表

#### 3.3 architecture-map.md

**目的**: 架构映射和依赖关系文档。

**内容**:
- 分层依赖关系图（ASCII 艺术）
- 关键单例列表
- 数据库集合列表
- 生命周期事件

#### 3.4 code-patterns.md

**目的**: 编码模式和约定速查表。

**内容**:
- API 响应模式
- 数据库访问模式
- 模块执行模式
- 配置访问模式

### 4. 现有文档增强（可选）

为现有 Markdown 文件添加 YAML frontmatter，不修改内容主体：

```markdown
---
title: 架构设计
description: YiAi 项目的关键架构设计和实现模式
category: Architecture
tags: [FastAPI, MongoDB, 架构]
priority: high
ai-summary: 本文档详细介绍分层架构、模块执行引擎、配置系统、数据库单例等核心设计模式
---

(原有内容保持不变...)
```

## 实施计划

1. 创建 `docs/INDEX.md`
2. 创建 `docs/SUMMARY.md`
3. 创建 `docs/.context/` 目录
4. 创建 `docs/.context/project-overview.json`
5. 创建 `docs/.context/file-patterns.md`
6. 创建 `docs/.context/architecture-map.md`
7. 创建 `docs/.context/code-patterns.md`
8. 可选：为现有文档添加 YAML frontmatter

## 风险与注意事项

- **风险**: 维护额外的索引和元数据文件需要额外工作
- **缓解**: 保持元数据简洁，只在关键变更时更新
- **风险**: 文档可能过时
- **缓解**: 在 frontmatter 中添加 `last-updated` 字段

## 成功标准

- AI 编码助手能够更快地找到相关文档
- 项目结构清晰易懂
- 人类开发者的文档体验不受影响
- 所有现有文档保持可用
