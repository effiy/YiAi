# YiAi

基于 FastAPI 的 AI 服务后端，通过 REST API 端点提供丰富的功能。

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

## 📄 许可证

本项目采用内部项目许可证。

---

## 📖 更多信息

关于项目的更多详细信息，请参考 [CLAUDE.md](CLAUDE.md) 和 [docs/](docs/) 目录下的文档。
