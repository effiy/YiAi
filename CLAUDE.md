# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在使用此仓库代码时提供指导。

## 项目概述

YiAi 是一个基于 FastAPI 的 AI 服务后端，通过 REST API 端点提供 RSS 管理、文件上传、AI 聊天和动态模块执行功能。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python main.py
```

服务器运行在 http://localhost:8000，已启用自动重载。API 文档可通过 /docs 和 /redoc 访问。

## 关键命令

| 命令 | 用途 |
|---------|---------|
| `python main.py` | 启动开发服务器 |
| `python -m pytest tests/ -v` | 运行所有测试（如果存在测试） |

## 架构

### 高层结构

```
main.py (FastAPI 入口，兼容性包装器)
├── src/
│   ├── main.py (FastAPI 应用工厂与生命周期)
│   ├── api/routes/          # API 端点
│   │   ├── execution.py     # 动态模块执行
│   │   ├── upload.py        # 文件上传
│   │   ├── wework.py        # 企业微信集成
│   │   └── maintenance.py   # 维护端点
│   ├── core/                 # 核心基础设施
│   │   ├── config.py        # 配置（YAML + 环境变量）
│   │   ├── database.py      # MongoDB 单例
│   │   ├── logger.py        # 日志设置
│   │   ├── exceptions.py    # 自定义异常
│   │   ├── response.py      # 统一响应格式
│   │   ├── middleware.py    # 认证中间件
│   │   └── exception_handler.py # 异常处理器
│   ├── models/               # Pydantic 模型与集合
│   └── services/             # 业务逻辑
│       ├── execution/       # 模块执行器
│       ├── rss/             # RSS 源管理
│       ├── ai/              # Ollama 聊天服务
│       ├── storage/         # OSS 存储
│       ├── static/          # 静态文件服务
│       └── database/        # 数据访问
├── config.yaml             # 配置文件
└── tests/                  # 测试目录（如果存在）
```

### 关键架构模式

1. **模块执行引擎**：`/execution` 端点允许通过 GET/POST 动态执行任何白名单中的模块方法。支持同步/异步函数、生成器、异步生成器和 SSE 流式传输。

2. **配置系统**：使用 Pydantic Settings，结合 YAML 配置文件（`config.yaml`）+ 环境变量覆盖。嵌套的 YAML 键会被扁平化为蛇形命名（例如，`server.host` → `server_host`）。

3. **数据库**：通过 Motor 异步驱动实现 MongoDB 单例。通过 `core.database.db` 全局实例访问。

4. **生命周期管理**：FastAPI 生命周期在 `src/main.py` 中管理 MongoDB 连接和 RSS 调度器的启动/关闭。

## 配置

- 主要配置：`config.yaml`
- 环境变量覆盖 YAML 配置（大写、蛇形命名）
- 通过 `core.config.settings` 单例访问

**重要配置**：
- `module.allowlist`：模块执行白名单（使用 `["*"]` 表示全部）
- `mongodb.url`：MongoDB 连接字符串
- `static.base_dir`：静态文件目录
- `rss.scheduler_interval`：RSS 轮询间隔（秒）
- `middleware.auth_enabled`：启用/禁用令牌认证

## 数据库集合

- `sessions`：用户会话
- `rss`：RSS 文章
- `chat_records`：聊天历史
- `oss_file_info`：文件元数据
- `oss_file_tags`：文件标签

## API 端点

| 方法 | 路径 | 描述 |
|--------|------|-------------|
| GET/POST | `/execution` | 执行模块方法 |
| POST | `/upload` | 上传文件 |

## 模块执行（`services.execution.executor`）

执行引擎是 YiAi 可扩展性的核心：

- 通过 `config.yaml` > `module.allowlist` 控制白名单
- 支持异步/同步函数、生成器、异步生成器
- 自动检测函数类型并适当处理
- 参数可以是字典或 JSON 字符串
- 为生成器函数提供 SSE 流式传输

**示例**：
```python
await execute_module(
    module_path="module.path",
    function_name="function_name",
    parameters={"key": "value"}
)
```

## 入口点

- **根目录 `main.py`**：兼容性包装器，将 `src/` 添加到路径并从 `src.main` 导入
- **`src/main.py`**：实际的 FastAPI 应用，包含 `create_app()` 工厂和默认 `app` 实例
- **两个文件** 可以互换使用来运行服务器
