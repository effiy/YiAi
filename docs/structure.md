# 项目目录结构

```
YiAi/
├── main.py                          # 兼容性入口文件
├── config.yaml                      # 主配置文件
├── requirements.txt                 # Python 依赖
├── CLAUDE.md                        # Claude Code 项目说明
├── .gitignore                       # Git 忽略文件
│
├── docs/                            # 文档目录
│   └── structure.md                 # 本文档 - 目录结构说明
│
├── logs/                            # 日志目录
│
└── src/                             # 源代码目录
    ├── main.py                      # FastAPI 应用入口（应用工厂）
    │
    ├── api/                         # API 层
    │   └── routes/                  # API 路由
    │       ├── execution.py         # 动态模块执行端点
    │       ├── upload.py            # 文件上传端点
    │       ├── wework.py            # 企业微信集成端点
    │       └── maintenance.py       # 维护端点
    │
    ├── core/                        # 核心基础设施
    │   ├── config.py                # 配置管理（YAML + 环境变量）
    │   ├── database.py              # MongoDB 单例
    │   ├── logger.py                # 日志设置
    │   ├── exceptions.py            # 自定义异常
    │   ├── error_codes.py           # 错误码定义
    │   ├── response.py              # 统一响应格式
    │   ├── middleware.py            # 认证中间件
    │   └── exception_handler.py     # 全局异常处理器
    │
    ├── models/                      # 数据模型
    │   └── schemas.py               # Pydantic 模型定义
    │
    └── services/                    # 业务逻辑层
        ├── execution/               # 模块执行引擎
        │   └── executor.py          # 模块执行器
        │
        ├── rss/                     # RSS 源管理
        │   ├── scheduler.py         # RSS 调度器
        │   └── parser.py            # RSS 解析器
        │
        ├── ai/                      # AI 聊天服务
        │   └── ollama_client.py     # Ollama 客户端
        │
        ├── storage/                 # 存储服务
        │   └── oss_client.py        # OSS 存储客户端
        │
        ├── static/                  # 静态文件服务
        │   └── file_manager.py      # 文件管理器
        │
        └── database/                # 数据访问层
            └── crud.py              # 通用 CRUD 操作
```

## 目录说明

### 根目录文件
- `main.py`: 兼容性包装器，添加 src/ 到路径并导入实际应用
- `config.yaml`: 主要配置文件，包含服务器、数据库、OSS、RSS 等配置
- `requirements.txt`: Python 依赖包列表
- `CLAUDE.md`: Claude Code 使用此仓库时的指导文档

### 核心目录

#### `/src/` - 源代码主目录
- `main.py`: FastAPI 应用工厂，包含生命周期管理（MongoDB 连接、RSS 调度器等）

#### `/src/api/routes/` - API 端点
- `execution.py`: 动态模块执行端点，支持通过 GET/POST 执行白名单中的模块方法
- `upload.py`: 文件上传端点，包括 OSS 上传和本地存储上传
- `wework.py`: 企业微信集成相关端点
- `maintenance.py`: 系统维护端点

#### `/src/core/` - 核心基础设施
- `config.py`: 使用 Pydantic Settings 管理配置，支持 YAML + 环境变量覆盖
- `database.py`: MongoDB 异步连接单例
- `logger.py`: 日志配置
- `exceptions.py`: 自定义业务异常
- `error_codes.py`: 错误码常量定义
- `response.py`: 统一 API 响应格式
- `middleware.py`: 认证中间件
- `exception_handler.py`: 全局异常处理器

#### `/src/models/` - 数据模型
- `schemas.py`: Pydantic 请求/响应模型

#### `/src/services/` - 业务逻辑
- `execution/executor.py`: 模块执行引擎，支持同步/异步函数、生成器、SSE 流式传输
- `rss/`: RSS 源管理和调度
- `ai/ollama_client.py`: Ollama AI 聊天服务客户端
- `storage/oss_client.py`: AliCloud OSS 存储服务封装
- `static/file_manager.py`: 静态文件管理
- `database/crud.py`: 数据库 CRUD 操作

### 其他目录
- `/docs/`: 项目文档
- `/logs/`: 日志文件存放目录
