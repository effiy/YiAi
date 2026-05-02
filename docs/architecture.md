# 架构设计

> 项目架构约定与模块放置规则

---

## 目录组织

```
main.py                      # 根入口（兼容性包装器）
src/
├── main.py                  # FastAPI 应用工厂与生命周期
├── __main__.py              # python -m src 启动入口
├── api/
│   ├── __init__.py
│   ├── deps.py              # 依赖注入（预留）
│   └── routes/
│       ├── __init__.py
│       ├── execution.py     # 动态模块执行端点
│       ├── upload.py        # 文件上传/管理端点
│       ├── wework.py        # 企业微信集成端点
│       └── maintenance.py   # 维护端点（清理等）
├── core/
│   ├── __init__.py
│   ├── config.py            # Pydantic Settings + YAML 配置
│   ├── database.py          # MongoDB 单例（Motor）
│   ├── logger.py            # 日志配置
│   ├── exceptions.py        # 业务异常基类
│   ├── response.py          # 统一响应封装
│   ├── middleware.py        # 认证中间件
│   ├── exception_handler.py # 全局异常处理器注册
│   ├── error_codes.py       # 错误码枚举
│   └── utils.py             # 通用工具函数
├── models/
│   ├── __init__.py
│   ├── schemas.py           # Pydantic 请求/响应模型
│   └── collections.py       # 集合定义（预留）
└── services/
    ├── __init__.py
    ├── execution/
    │   └── executor.py      # 受控模块执行器
    ├── rss/
    │   ├── feed_service.py  # RSS 抓取与解析
    │   └── rss_scheduler.py # APScheduler 定时调度
    ├── ai/
    │   └── chat_service.py  # Ollama 聊天服务
    ├── storage/
    │   └── oss_client.py    # 阿里云 OSS 客户端
    ├── static/
    │   ├── static_files.py  # 静态文件服务
    │   └── archive_service.py # 归档服务
    └── database/
        ├── data_service.py  # 数据访问服务
        └── mongo_store.py   # MongoDB 存储封装
```

## 放置规则

| 类型 | 放置位置 | 禁止行为 |
|------|---------|---------|
| API 路由 | `src/api/routes/` | 禁止在路由中写业务逻辑 |
| 业务逻辑 | `src/services/<域>/` | 禁止直接操作数据库连接 |
| 数据模型 | `src/models/schemas.py` | 禁止在模型中引入框架依赖 |
| 核心基础设施 | `src/core/` | 禁止在 core 中引用 services |
| 配置 | `src/core/config.py` + `config.yaml` | 禁止硬编码配置值 |
| 工具函数 | `src/core/utils.py` | 禁止在 utils 中引入业务逻辑 |

## 核心架构模式

### 1. 应用工厂模式

`src/main.py` 中的 `create_app()` 允许通过参数控制认证、数据库和 RSS 初始化行为，便于测试和不同环境部署。

```python
def create_app(
    *,
    enable_auth: bool | None = None,
    init_db: bool | None = None,
    init_rss: bool | None = None,
) -> FastAPI:
    ...
```

### 2. 单例模式（数据库）

`core.database.MongoDB` 使用 `__new__` 实现单例，全局通过 `db = MongoDB()` 访问。

### 3. 统一响应格式

所有 API 返回 `StandardResponse` 结构：`{code, message, data}`，通过 `core.response.success()` / `fail()` 构造。

### 4. 受控模块执行

通过白名单控制可动态执行的模块方法，支持同步/异步/生成器/SSE 流式传输。

### 5. 双重存储策略

文件上传优先 OSS，OSS 不可用时自动 fallback 到本地静态存储。

### 6. MCP 服务器集成

通过 `fastapi-mcp` 在 `src/main.py` 中创建并挂载 MCP 服务器，自动将 FastAPI 端点暴露为 Model Context Protocol 服务，`Maintenance` 标签的端点被排除。

```python
from fastapi_mcp import FastApiMCP

mcp = FastApiMCP(
    app,
    name="YiAi MCP",
    describe_all_responses=True,
    describe_full_response_schema=True,
    exclude_tags=["Maintenance"]
)
mcp.mount()
```

## 模块结构

| 模块 | 职责 | 关键文件 |
|------|------|---------|
| execution | 动态模块执行引擎 | `services/execution/executor.py` |
| upload | 文件上传与管理 | `api/routes/upload.py`, `services/storage/oss_client.py` |
| rss | RSS 源管理与定时抓取 | `services/rss/feed_service.py`, `services/rss/rss_scheduler.py` |
| ai | Ollama AI 聊天 | `services/ai/chat_service.py` |
| wework | 企业微信机器人 | `api/routes/wework.py` |
| maintenance | 系统维护（清理等） | `api/routes/maintenance.py` |
| mcp | MCP 协议服务 | `src/main.py` (FastApiMCP 挂载) |

## 编码规范

- 模块/文件：snake_case
- 类名：CapWords
- 函数/方法：snake_case
- 常量：UPPER_SNAKE_CASE
- 类型注解：所有函数参数和返回值必须有类型注解
- 文档字符串：Google 风格

## 实施顺序

1. 核心基础设施（config, database, response, exceptions, error_codes）
2. 通用工具（logger, utils, middleware, exception_handler）
3. 数据模型（schemas）
4. 业务服务（execution, storage, rss, ai）
5. API 路由（execution, upload, wework, maintenance）
6. 应用组装（main.py）
7. 入口包装（根 main.py）
