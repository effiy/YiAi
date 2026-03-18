# YiAi 项目文档

欢迎使用 YiAi 项目文档！

## 📋 项目概述

YiAi 是一个基于 FastAPI 的 AI 服务后端，通过 REST API 端点提供以下功能：

- 📰 RSS 源管理
- 📤 文件上传（支持 OSS 和本地存储）
- 🤖 AI 聊天（Ollama 集成）
- ⚡ 动态模块执行

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

1. 复制并编辑 `config.yaml` 配置文件
2. 根据需要配置 MongoDB、OSS、RSS 等设置
3. 环境变量可以覆盖 YAML 配置（大写、蛇形命名）

### 启动开发服务器

```bash
python main.py
```

服务器将在 http://localhost:8000 启动，已启用自动重载。

### 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 文档目录

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

### 关键特性

1. **模块执行引擎**：`/execution` 端点允许通过 GET/POST 动态执行任何白名单中的模块方法
2. **配置系统**：使用 Pydantic Settings，结合 YAML 配置文件 + 环境变量覆盖
3. **数据库**：通过 Motor 异步驱动实现 MongoDB 单例
4. **生命周期管理**：FastAPI 生命周期管理 MongoDB 连接和 RSS 调度器

## 📖 更多信息

关于项目的更多详细信息，请参考项目根目录下的 [CLAUDE.md](../CLAUDE.md) 文件。
