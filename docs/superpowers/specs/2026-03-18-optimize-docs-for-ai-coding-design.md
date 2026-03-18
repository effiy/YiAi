# 优化 docs 目录以适应 AI 编码 - 设计文档

**日期**: 2026-03-18
**项目**: YiAi
**状态**: 待审核

---

## 概述

本设计文档描述了如何优化 YiAi 项目的 `docs/` 目录，使其更适合 AI 编码助手（如 Claude Code）理解和使用，同时保持对人类开发者的友好性。

## 目标

1. **更好的 AI 理解** - 帮助 AI 编码助手更快、更准确地理解项目
2. **更清晰的结构** - 提供更好的导航和逻辑分组
3. **结构化约定** - 清晰的命名、一致的模式和明确的组织
4. **快速参考** - 简洁的摘要、速查表和查找表
5. **机器可读** - 格式良好的 Markdown、YAML 等，便于 AI 解析

## 与 CLAUDE.md 的关系

本设计**补充**而不是替代项目根目录下的 `CLAUDE.md` 文件：

- **CLAUDE.md**（根目录）- 面向 AI 的项目级别快速入门指南，提供最核心的信息
- **docs/** 目录增强 - 提供更详细、结构化的文档导航和深度上下文
- **分工明确**：CLAUDE.md 用于快速上手，docs/.context/ 用于深度开发参考

## 设计方案：方案 1 - 结构化增强 + AI 友好化

### 核心原则

- **非破坏性** - 不删除、不重命名任何现有文件
- **增量式** - 只添加新文件，不修改现有内容
- **双重优化** - 同时优化机器可读性和结构化导航
- **保持中文命名** - 所有现有中文文件名保持不变

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
│   │   ├── README.md
│   │   ├── AI聊天服务.md
│   │   ├── RSS源管理.md
│   │   ├── 文件上传与存储.md
│   │   ├── 动态模块执行引擎.md
│   │   └── 安全与认证.md
│   └── 开发规范/
│       ├── README.md
│       ├── 项目概述.md
│       ├── 编码规范.md
│       ├── 项目结构.md
│       ├── 样式规范.md
│       ├── 文档规范.md
│       ├── 组件规范.md
│       ├── API规范.md
│       ├── 路由规范.md
│       ├── 状态管理.md
│       ├── 数据库规范.md
│       ├── 安全规范.md
│       ├── 日志规范.md
│       ├── 错误处理规范.md
│       ├── 通用约束.md
│       ├── 测试规范.md
│       ├── Git提交规范.md
│       └── 部署规范.md
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

`.context/` 目录提供比 `CLAUDE.md` 更详细的参考信息，专为深度开发任务设计。

#### 3.1 project-overview.json

**目的**: 提供机器可读的结构化项目概览，便于 AI 快速解析。

**为什么 JSON 格式**：
- JSON 是结构化数据的标准格式，AI 可以可靠地解析
- 避免了 Markdown 中自然语言的歧义
- 便于程序化生成和验证
- Claude Code 等工具对 JSON 有特殊优化

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
  },
  "docsIndex": "docs/INDEX.md",
  "claudeGuide": "CLAUDE.md"
}
```

#### 3.2 file-patterns.md

**目的**: 关键文件路径和用途速查表，比 CLAUDE.md 中的信息更详尽。

**内容**:
- 入口点表格
- API 路由表格
- 核心服务表格
- 数据库集合列表

#### 3.3 architecture-map.md

**目的**: 架构映射和依赖关系文档，提供可视化的架构理解。

**内容**:
- 分层依赖关系图（ASCII 艺术）
- 关键单例列表
- 数据库集合列表
- 生命周期事件

#### 3.4 code-patterns.md

**目的**: 编码模式和约定速查表，提供可复制的代码示例。

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
last-updated: 2026-03-18
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
- **风险**: 与 CLAUDE.md 内容重叠
- **缓解**: 明确分工 - CLAUDE.md 用于快速入门，docs/.context/ 用于深度参考

## AI 友好性设计说明

为什么这些改进有助于 AI 编码：

1. **结构化索引** - INDEX.md 和 SUMMARY.md 提供了文档的完整地图，AI 不必猜测或搜索
2. **机器可读格式** - JSON 格式的 project-overview.json 可以被可靠解析，没有歧义
3. **速查表设计** - file-patterns.md 和 code-patterns.md 采用表格格式，便于 AI 快速查找信息
4. **YAML frontmatter** - 为每个文档添加元数据，帮助 AI 理解文档的目的和优先级
5. **集中化上下文** - .context/ 目录将 AI 需要的所有参考信息集中在一处

## 成功标准

- AI 编码助手能够更快地找到相关文档
- 项目结构清晰易懂
- 人类开发者的文档体验不受影响
- 所有现有文档保持可用
- 与 CLAUDE.md 形成互补，而不是重复
