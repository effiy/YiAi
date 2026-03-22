# YiAi

[项目概述](#-项目概述) | [核心功能](#-核心功能) | [技术栈](#-技术栈) | [快速开始](#-快速开始) | [文档](#-文档) | [架构](#-架构) | [关键命令](#-关键命令) | [故障排除](#-故障排除) | [更新日志](#-更新日志) | [更多信息](#-更多信息)

---

## 📋 项目概述

YiAi 是一个基于 FastAPI 的 AI 服务后端，通过 REST API 端点提供丰富的功能。它采用模块化设计，支持动态扩展，集成了 AI 聊天、RSS 管理、文件存储等多种能力。

---

## ✨ 核心功能

- 🤖 **AI 聊天服务** - 集成 Ollama 本地 AI 模型，支持多轮对话和历史记录
- 📰 **RSS 源管理** - 自动定时抓取 RSS 源内容，支持多源管理
- 📤 **文件上传与存储** - 支持 OSS 和本地存储双重方案，完整的文件管理功能
- ⚡ **动态模块执行引擎** - 通过 REST API 动态执行 Python 模块方法
- 🛡️ **安全与认证** - 可选的令牌认证，统一的异常处理

---

## 🛠️ 技术栈

- **Web 框架** - FastAPI (高性能异步框架)
- **ASGI 服务器** - Uvicorn
- **数据验证** - Pydantic v2
- **数据库** - MongoDB (Motor 异步驱动)
- **AI 集成** - Ollama (本地 LLM)
- **RSS 处理** - feedparser
- **任务调度** - APScheduler
- **对象存储** - 阿里云 OSS (oss2)
- **配置管理** - Pydantic Settings + YAML
- **文件处理** - python-multipart, aiofiles
- **HTTP 客户端** - aiohttp
- **重试机制** - tenacity

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

## 📖 文档

详细文档请查看 [docs/README.md](docs/README.md)。

### 主要文档

- [项目文档首页](docs/README.md)
- [核心功能](docs/核心功能/README.md) - 采用敏捷需求管理方式组织
- [API端点](docs/API端点.md)
- [架构设计](docs/架构设计.md)
- [项目结构](docs/项目结构.md)
- [配置指南](docs/配置指南.md)
- [开发规范](docs/开发规范/README.md)

---

## 🏗️ 架构

YiAi 采用经典的分层架构设计：

- **API 层** (`src/api/routes/`) - 处理 HTTP 请求和响应
- **业务逻辑层** (`src/services/`) - 实现核心业务功能
- **核心基础设施层** (`src/core/`) - 配置、数据库、日志等基础服务
- **数据模型层** (`src/models/`) - Pydantic 数据模型和数据库集合

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

记录项目的版本历史和重要变更。详细的更新日志请参考 [docs/更新日志.md](docs/更新日志.md)。

| 版本 | 日期 | 说明 |
|------|------|------|
| [未发布] | - | 文档重构，采用敏捷需求管理方式组织 |
| [0.3.0] | 2026-03-19 | 新增完整开发规范文档体系，重组文档目录结构 |
| [0.2.0] | 2026-03-16 | 新增本地存储 fallback 机制 |
| [0.1.0] | 2026-03-13 | 新增 CLAUDE.md 文档，重组文档结构 |
| [0.0.1] | 2026-03-11 | 初始项目提交，核心功能基础架构 |

---

## 📖 更多信息

关于项目的更多详细信息，请参考 [CLAUDE.md](CLAUDE.md) 和 [docs/](docs/) 目录下的文档。
