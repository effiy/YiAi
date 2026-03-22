# YiAi

[项目概述](#项目概述) | [技术栈](#技术栈) | [快速开始](#快速开始) | [关键命令](#关键命令) | [故障排除](#故障排除) | [更新日志](#更新日志) | [更多信息](#更多信息)

---

## 📋 项目概述

YiAi 是一个基于 FastAPI 的 AI 服务后端，通过 REST API 端点提供丰富的功能。它采用模块化设计，支持动态扩展，集成了 AI 聊天、RSS 管理、文件存储等多种能力。

### 核心功能

- 🤖 **AI 聊天服务** - 集成 Ollama 本地 AI 模型，支持多轮对话和历史记录
- 📰 **RSS 源管理** - 自动定时抓取 RSS 源内容，支持多源管理
- 📤 **文件上传与存储** - 支持 OSS 和本地存储双重方案，完整的文件管理功能
- ⚡ **动态模块执行引擎** - 通过 REST API 动态执行 Python 模块方法
- 🛡️ **安全与认证** - 可选的令牌认证，统一的异常处理

---

## 🛠️ 技术栈

| 类别 | 框架/技术/库 | 用途说明 |
|------|-------------|---------|
| Web 框架 | 🚀 FastAPI | 高性能异步 Web 框架，自动生成 API 文档 |
| ASGI 服务器 | 🔌 Uvicorn | 生产级 ASGI 服务器，支持热重载 |
| 数据验证 | ✅ Pydantic v2 | 类型提示驱动的数据验证和序列化 |
| 数据库 | 💾 MongoDB + Motor | NoSQL 数据库 + 异步 Python 驱动 |
| AI 集成 | 🤖 Ollama | 本地 LLM 运行时，支持多种开源模型 |
| RSS 处理 | 📰 feedparser | RSS/Atom 源解析库 |
| 任务调度 | ⏰ APScheduler | 定时任务调度框架，支持多种触发器 |
| 对象存储 | ☁️ 阿里云 OSS (oss2) | 阿里云对象存储服务 SDK |
| 配置管理 | ⚙️ Pydantic Settings + YAML | 类型安全的配置管理，支持环境变量覆盖 |
| 文件处理 | 📁 python-multipart, aiofiles | 多部分表单解析 + 异步文件操作 |
| HTTP 客户端 | 🌐 aiohttp | 异步 HTTP 客户端/服务器库 |
| 重试机制 | 🔄 tenacity | 通用重试库，支持多种重试策略 |

---

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

1. 复制并编辑 `config.yaml` 配置文件
2. 根据需要配置各项参数
3. 环境变量可以覆盖 YAML 配置（大写、蛇形命名，如 `SERVER_HOST`）

### 启动开发服务器

```bash
python main.py
```

服务器将在 http://localhost:8000 启动，已启用自动重载。

API 文档可通过 /docs 和 /redoc 访问。

---

## 🔧 关键命令

| 命令 | 用途 |
|--------|------|
| `python main.py` | 启动开发服务器 |
| `python -m pytest tests/ -v` | 运行所有测试（如果存在） |

---

## 🔧 故障排除

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 🚫 服务器启动失败，提示 "ModuleNotFoundError" | 依赖包未正确安装 | 运行 `pip install -r requirements.txt` 重新安装依赖 |
| ⏱️ MongoDB 连接超时 | MongoDB 服务未启动或连接地址错误 | 确认 `mongodb.url` 配置正确，检查 MongoDB 服务状态 |
| 🤖 Ollama 请求失败 | Ollama 服务未运行或地址配置错误 | 确认 `ollama.url` 配置正确，检查 Ollama 服务是否在运行 |
| 📤 文件上传到 OSS 失败 | OSS 配置不正确或网络问题 | 检查 `oss.access_key`、`oss.secret_key`、`oss.bucket` 等配置，确认网络连接正常 |
| 📰 RSS 定时任务不执行 | RSS 调度器未启用 | 确认 `rss.scheduler_enabled` 设置为 `true` |
| 🔐 API 返回 401 未授权 | 认证中间件已启用但未提供令牌 | 在请求头中添加 `X-Token: <your-token>`，或临时禁用 `middleware.auth_enabled` |
| ⚡ 动态模块执行提示 "not in allowlist" | 模块未在白名单中 | 在 `module.allowlist` 中添加所需模块，或使用 `["*"]` 允许所有模块 |
| 📁 静态文件无法访问 | 静态文件目录配置错误 | 检查 `static.base_dir` 路径是否存在且有正确的权限 |

---

## 📝 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| [未发布] | - | 文档重构，采用敏捷需求管理方式组织 |
| [0.3.0] | 2026-03-19 | 新增完整开发规范文档体系，重组文档目录结构 |
| [0.2.0] | 2026-03-16 | 新增本地存储 fallback 机制 |
| [0.1.0] | 2026-03-13 | 新增 CLAUDE.md 文档，重组文档结构 |
| [0.0.1] | 2026-03-11 | 初始项目提交，核心功能基础架构 |

记录项目的版本历史和重要变更。详细的更新日志请参考 [docs/更新日志.md](docs/更新日志.md)。

---

## 📖 更多信息

关于项目的更多详细信息，请参考 [CLAUDE.md](CLAUDE.md) 和 [docs/](docs/) 目录下的文档。
