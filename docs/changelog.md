# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- State Store 服务：结构化状态记录 CRUD（`StateStoreService`）
- SkillRecorder：fire-and-forget 技能执行记录
- SessionAdapter：遗留 session 文档转换为结构化模型
- Observer Reliability 系统：ThrottleMiddleware（限流）、TailSampler（采样）、SandboxMiddleware（沙箱）、LazyStartManager（懒启动）、ReentrancyGuard（重入守卫）
- CLI 工具：`src/cli/state_query.py`（typer + rich），支持 list/get/export/stats
- 新 API 端点：`/state/records`（CRUD）、`/health/observer`（Observer 健康检查）
- 新数据库集合：`state_records`
- 新依赖：typer>=0.9.0、rich>=13.0.0、tenacity>=8.2.3
- 新配置段：`state_store`、`observer`（14 字段）、`uvicorn`
- 文档重构，采用敏捷需求管理方式组织
- 项目初始化文档体系（docs/project-init/01-07）

## [0.3.0] - 2026-03-19

### Added
- 新增完整开发规范文档体系
- 重组文档目录结构

## [0.2.0] - 2026-03-16

### Added
- 新增本地存储 fallback 机制

## [0.1.0] - 2026-03-13

### Added
- 新增 CLAUDE.md 文档
- 重组文档结构

## [0.0.1] - 2026-03-11

### Added
- 初始项目提交
- 核心功能基础架构（FastAPI + MongoDB + 动态模块执行）
- 文件上传与管理
- RSS 源管理
- AI 聊天服务（Ollama）
- 企业微信机器人集成
