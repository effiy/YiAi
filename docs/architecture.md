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
│       ├── execution.py       # 动态模块执行端点
│       ├── upload.py          # 文件上传/管理端点
│       ├── wework.py          # 企业微信集成端点
│       ├── maintenance.py     # 维护端点（清理等）
│       ├── state.py           # 结构化状态记录 CRUD
│       └── observer_health.py # Observer 运行时健康检查
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
│   ├── utils.py             # 通用工具函数
│   └── observer/            # Observer Reliability 组件
│       ├── __init__.py
│       ├── throttle.py      # 固定窗口请求限流
│       ├── sampler.py       # 尾部采样（慢/错误请求）
│       ├── sandbox.py       # 文件系统/网络沙箱
│       ├── lazy_start.py    # 懒启动管理器
│       └── guard.py         # 重入深度守卫
├── models/
│   ├── __init__.py
│   ├── schemas.py           # Pydantic 请求/响应模型
│   └── collections.py       # 集合定义
├── services/
│   ├── __init__.py
│   ├── execution/
│   │   └── executor.py      # 受控模块执行器
│   ├── rss/
│   │   ├── feed_service.py  # RSS 抓取与解析
│   │   └── rss_scheduler.py # APScheduler 定时调度
│   ├── ai/
│   │   └── chat_service.py  # Ollama 聊天服务
│   ├── storage/
│   │   └── oss_client.py    # 阿里云 OSS 客户端
│   ├── static/
│   │   ├── static_files.py  # 静态文件服务
│   │   └── archive_service.py # 归档服务
│   ├── state/
│   │   ├── state_service.py     # 状态存储 CRUD
│   │   ├── skill_recorder.py    # 技能执行记录（fire-and-forget）
│   │   └── session_adapters.py  # 遗留 session 文档转换
│   └── database/
│       ├── data_service.py  # 数据访问服务
│       └── mongo_store.py   # MongoDB 存储封装
└── cli/
    └── state_query.py       # 状态查询 CLI 工具（typer）
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
| Observer 组件 | `src/core/observer/` | 禁止在 observer 中引用 services 层 |
| State 服务 | `src/services/state/` | 禁止在 state 路由中直接操作数据库 |
| CLI 工具 | `src/cli/` | 禁止在 CLI 中启动 FastAPI 服务 |

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

**MCP 请求生命周期**：AI 客户端 → mcp-proxy (npx) → HTTPS → `/mcp` SSE 端点 → Auth（/mcp* 白名单免 Token）→ Observer 中间件栈（Throttle → Sampler）→ FastApiMCP 工具分发 → 路由处理器 → SSE 响应。

**MCP 工具命名规则**：工具名由 FastAPI 路由的 `operation_id` 生成，格式为英文 `snake_case` 动词_名词（如 `create_state_record`、`query_state_records`）。未设置 `operation_id` 时 fastapi-mcp 会自动生成不可控名称，因此所有非 Maintenance 端点均应显式设置。

**MCP 端点认证**：`/mcp*` 路径在 Auth 中间件中白名单化（`middleware.py:68`），无需 `X-Token`。安全依赖网络层 IP 白名单和 Observer 限流保护。

**MCP 安全注意事项**：`module.allowlist: ["*"]` 配置下 MCP 可调用任意模块方法。面向公网部署时建议在反向代理层增加 IP 限制。

完整工具清单和使用指南见 [docs/mcp-service-optimization/](./mcp-service-optimization/03_design-document.md)。

### 7. State Store 服务

结构化状态记录的完整 CRUD 服务，包含三个子组件：

- **StateStoreService**（`services/state/state_service.py`）：提供 create/query/get/update/delete 操作，支持按 record_type、tags、title 等条件过滤查询，分页结果带 total/pageNum/totalPages。
- **SkillRecorder**（`services/state/skill_recorder.py`）：fire-and-forget 模式，通过 `asyncio.create_task` 异步记录技能执行信息，失败不传播给调用者。
- **SessionAdapter**（`services/state/session_adapters.py`）：将 `sessions` 集合中的遗留文档转换为结构化 `SessionState` Pydantic 模型。

```python
from services.state.state_service import StateStoreService

service = StateStoreService()
result = await service.create({"record_type": "skill_execution", "title": "..."})
records = await service.query(record_type="skill_execution", page_num=1, page_size=20)
```

REST API 通过 `src/api/routes/state.py` 暴露 `/state/records` 端点（5 个操作），CLI 工具通过 `src/cli/state_query.py` 提供 `list`/`get`/`export`/`stats` 命令。

### 8. Observer Reliability 系统

5 个组件的可靠性监控系统，全部位于 `src/core/observer/`：

| 组件 | 文件 | 功能 |
|------|------|------|
| ThrottleMiddleware | `throttle.py` | 固定窗口 IP 限流，超限返回 429 + `code:1003` |
| TailSampler + SamplerMiddleware | `sampler.py` | 尾部采样，记录慢请求（>slow_threshold_ms）或错误（>=500）到环形缓冲区 |
| SandboxMiddleware | `sandbox.py` | 文件系统和网络访问控制，通过 `sandbox_context()` 上下文管理器使用（非 HTTP 中间件） |
| LazyStartManager | `lazy_start.py` | 重型组件懒启动，`asyncio.Lock` 线程安全 |
| ReentrancyGuard | `guard.py` | 基于 `contextvars.ContextVar` 的重入深度守卫，超限抛出 `ReentrancyExceeded` |

中间件注册顺序（在 `create_app()` 中，按请求处理由外到内）：Auth → CORS → Throttle → Sampler（Throttle 和 Sampler 仅在 `observer_enabled: true` 时注册）

Observer 运行时健康状态通过 `GET /health/observer` 端点查询，返回 `ObserverHealth` 模型（9 个字段：throttle_enabled、throttle_active_ips、sampler_enabled、sampler_buffer_size、sampler_buffer_max、sandbox_enabled、sandbox_violations_total、guard_enabled、guard_current_max_depth）。

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
| state | 结构化状态记录 CRUD | `api/routes/state.py`, `services/state/state_service.py`, `services/state/skill_recorder.py`, `services/state/session_adapters.py` |
| observer | 可靠性监控（限流/采样/沙箱/守卫） | `api/routes/observer_health.py`, `core/observer/throttle.py`, `core/observer/sampler.py`, `core/observer/sandbox.py`, `core/observer/lazy_start.py`, `core/observer/guard.py` |
| cli | 命令行状态查询工具 | `cli/state_query.py` |

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

## Postscript: Future Planning & Improvements

- 评估引入文档-代码一致性自动验证脚本
- 考虑为架构模式编写交互式示例
- 建立架构决策记录（ADR）流程

## Workflow Standardization Review

1. **Repetitive labor identification**: 目录树和模块表的更新为机械操作，可基于文件系统扫描自动生成。
2. **Decision criteria missing**: 新增架构模式的标准（何时独立为模式 vs 并入已有模式）缺乏量化规则。
3. **Information silos**: 架构模式和模块结构的信息在 CLAUDE.md、README.md、project-init/03 中重复维护。
4. **Feedback loop**: 架构文档与代码不一致时缺乏自动通知，依赖人工 re-init。

## System Architecture Evolution Thinking

- **A1. Current architecture bottleneck**: 架构模式描述为纯文本，缺乏与代码的直接可验证链接。
- **A2. Next natural evolution node**: 引入架构 lint 工具，基于 AST 扫描自动验证模式描述与代码实现的一致性。
- **A3. Risks and rollback plans for evolution**: AST 解析可能无法覆盖动态模式（如中间件注册）。回退方案：保持文本描述为主，lint 作为补充验证。
