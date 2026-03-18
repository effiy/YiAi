# YiAi 项目文档

欢迎使用 YiAi 项目文档！

## 📋 项目概述

YiAi 是一个基于 FastAPI 的 AI 服务后端，通过 REST API 端点提供丰富的功能。它采用模块化设计，支持动态扩展，集成了 AI 聊天、RSS 管理、文件存储等多种能力。

## ✨ 核心功能

- 🤖 **AI 聊天服务** - 集成 Ollama 本地 AI 模型，支持多轮对话和历史记录
- 📰 **RSS 源管理** - 自动定时抓取 RSS 源内容，支持多源管理
- 📤 **文件上传与存储** - 支持 OSS 和本地存储双重方案，完整的文件管理功能
- ⚡ **动态模块执行引擎** - 通过 REST API 动态执行 Python 模块方法
- 🛡️ **安全与认证** - 可选的令牌认证，统一的异常处理

详细的功能介绍请参考 [核心功能介绍](./features.md)。

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

1. 复制并编辑 `config.yaml` 配置文件
2. 根据需要配置以下项：
   - **MongoDB**：数据库连接信息
   - **OSS**：阿里云 OSS 存储配置（可选，未配置时使用本地存储）
   - **RSS**：调度器开关和抓取间隔
   - **Ollama**：AI 服务连接配置
   - **静态文件**：本地存储路径和访问 URL
3. 环境变量可以覆盖 YAML 配置（大写、蛇形命名，如 `SERVER_HOST`）

### 启动开发服务器

```bash
python main.py
```

服务器将在 http://localhost:8000 启动，已启用自动重载。

### 访问 API 文档

- **Swagger UI**：http://localhost:8000/docs - 交互式 API 文档
- **ReDoc**：http://localhost:8000/redoc - 更美观的 API 文档

## 📚 文档目录

- [核心功能介绍](./features.md) - 详细的功能说明
- [项目目录结构](./structure.md) - 了解项目的完整目录结构

## 🔧 关键命令

| 命令 | 用途 |
|--------|------|
| `python main.py` | 启动开发服务器 |
| `python -m pytest tests/ -v` | 运行所有测试（如果存在） |

## 🏗️ 架构简介

### 目录结构

```
YiAi/
├── main.py          # 🚀 兼容性入口文件
├── config.yaml      # ⚙️ 主配置文件
├── src/             # 💻 源代码目录
│   ├── main.py      # 🎯 FastAPI 应用入口
│   ├── api/routes/  # 🌐 API 端点
│   ├── core/        # 🏗️ 核心基础设施
│   ├── models/      # 📊 数据模型
│   └── services/    # ⚙️ 业务逻辑
└── docs/            # 📚 文档目录
```

详细的目录结构说明请参考 [structure.md](./structure.md)。

### 关键架构模式

1. **模块执行引擎**：`/execution` 端点允许通过 GET/POST 动态执行任何白名单中的模块方法，支持同步/异步函数、生成器、异步生成器和 SSE 流式传输

2. **配置系统**：使用 Pydantic Settings，结合 YAML 配置文件（`config.yaml`）+ 环境变量覆盖。嵌套的 YAML 键会被扁平化为蛇形命名（例如，`server.host` → `server_host`）

3. **数据库**：通过 Motor 异步驱动实现 MongoDB 单例。通过 `core.database.db` 全局实例访问

4. **生命周期管理**：FastAPI 生命周期在 `src/main.py` 中管理 MongoDB 连接和 RSS 调度器的启动/关闭

## 📊 数据库集合

- `sessions` - 用户会话
- `rss` - RSS 文章
- `chat_records` - 聊天历史
- `oss_file_info` - 文件元数据
- `oss_file_tags` - 文件标签
- `pet_data_sync` - 宠物数据同步（如适用）
- `seeds` - 种子数据（如适用）

## 🌐 API 端点概览

| 方法 | 路径 | 描述 |
|------|------|------|
| GET/POST | `/execution` | 动态执行模块方法 |
| POST | `/upload` | 文件上传 |
| POST | `/upload-image-to-oss` | 图片上传到 OSS（支持本地存储 fallback） |
| POST | `/read-file` | 读取文件内容 |
| POST | `/write-file` | 写入文件 |
| POST | `/delete-file` | 删除文件 |
| POST | `/delete-folder` | 删除文件夹 |
| POST | `/rename-file` | 重命名文件 |
| POST | `/rename-folder` | 重命名文件夹 |

更多 API 详情请访问 `/docs` 或 `/redoc`。

## 📖 更多信息

关于项目的更多详细信息，请参考项目根目录下的 [CLAUDE.md](../CLAUDE.md) 文件。
