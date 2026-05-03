# 项目初始化设计文档

> 模块划分、接口约定与架构约束。

---

## 1. 模块划分

```
src/
├── main.py              # 应用工厂与生命周期
├── api/routes/          # API 端点（无业务逻辑）
├── core/                # 核心基础设施（含 observer/ 组件）
├── models/              # Pydantic 模型与集合定义
├── services/            # 业务逻辑（含 state/ 服务）
└── cli/                 # CLI 工具
```

## 2. 核心设计决策

### 2.1 应用工厂模式

`create_app()` 允许通过参数控制认证、数据库和 RSS 初始化，便于测试和不同环境部署。

```python
def create_app(
    *,
    enable_auth: bool | None = None,
    init_db: bool | None = None,
    init_rss: bool | None = None,
) -> FastAPI:
    ...
```

### 2.2 单例数据库连接

`core.database.MongoDB` 通过 `__new__` 实现单例，全局通过 `db = MongoDB()` 访问。

### 2.3 统一响应格式

所有 API 返回 `StandardResponse`：`{code, message, data}`，通过 `core.response.success()` / `fail()` 构造。

### 2.4 受控模块执行

通过白名单控制可动态执行的模块方法，支持：
- 同步/异步函数
- 生成器 / 异步生成器
- SSE 流式传输（自动检测并包装）

### 2.5 MCP 服务器集成

`fastapi-mcp` 在应用创建后挂载，自动将 FastAPI 端点暴露为 MCP 服务。`Maintenance` 标签端点被排除。

### 2.6 State Store 服务

结构化状态记录的 CRUD 服务，三个子组件：

- **StateStoreService**：create/query/get/update/delete，支持 record_type、tags、title_contains 等过滤，`created_time` 降序分页。
- **SkillRecorder**：fire-and-forget 模式，`asyncio.create_task` 异步记录，失败仅记日志。
- **SessionAdapter**：遗留 session 文档转换为 `SessionState` Pydantic 模型。

### 2.7 Observer Reliability 系统

5 组件可靠性监控（全在 `core/observer/`）：

| 组件 | 功能 | 关键行为 |
|------|------|---------|
| ThrottleMiddleware | 固定窗口 IP 限流 | 超限返回 429 + code:1003 |
| TailSampler + SamplerMiddleware | 尾部采样 | 环形缓冲区记录慢/错误请求 |
| SandboxMiddleware | FS/网络访问控制 | 非 HTTP 中间件，通过 `sandbox_context()` 使用 |
| LazyStartManager | 懒启动初始化 | `asyncio.Lock` 线程安全 |
| ReentrancyGuard | 重入深度守卫 | `ContextVar`，超限抛 `ReentrancyExceeded` |

中间件栈顺序：Auth → Throttle → Sampler（仅在 `observer_enabled: true` 时注册）

## 3. 接口约定

### 3.1 API 路由清单

| 方法 | 路径 | 标签 | 说明 |
|------|------|------|------|
| GET/POST | `/execution` | Execution | 动态模块执行 |
| POST | `/upload` | Upload | 通用文件上传 |
| POST | `/upload-image-to-oss` | Upload | 图片上传到 OSS |
| POST | `/read-file` | Upload | 读取文件内容 |
| POST | `/write-file` | Upload | 写入文件 |
| POST | `/delete-file` | Upload | 删除文件 |
| POST | `/delete-folder` | Upload | 删除文件夹 |
| POST | `/rename-file` | Upload | 重命名文件 |
| POST | `/rename-folder` | Upload | 重命名文件夹 |
| POST | `/wework/send-message` | WeWork | 发送企业微信消息 |
| POST | `/cleanup-unused-images` | Maintenance | 清理未引用图片 |
| POST | `/state/records` | State | 创建状态记录 |
| GET | `/state/records` | State | 查询状态记录 |
| GET | `/state/records/{key}` | State | 获取单条状态记录 |
| PUT | `/state/records/{key}` | State | 更新状态记录 |
| DELETE | `/state/records/{key}` | State | 删除状态记录 |
| GET | `/health/observer` | Observer | Observer 运行时健康检查 |

### 3.2 错误码设计

| 范围 | 含义 |
|------|------|
| 0 | 成功 |
| 1xxx | 客户端错误（参数、认证、权限） |
| 5xxx | 服务端错误（内部、数据库） |

### 3.3 配置优先级

环境变量（大写蛇形命名）> `config.yaml` > 默认值

## 4. 数据模型

### 4.1 核心集合

- `sessions`：用户会话
- `rss`：RSS 文章（`link` 字段唯一索引）
- `chat_records`：聊天历史
- `oss_file_info`：文件元数据
- `oss_file_tags`：文件标签
- `pet_data_sync`：宠物数据同步
- `seeds`：种子数据
- `state_records`：结构化状态记录（技能执行记录、通用状态快照）

## 5. 安全约束

- 路径安全：禁止 `..` 和绝对路径（`_resolve_static_path`）
- 模块执行：白名单控制，生产环境禁止 `["*"]`
- 认证：可选 `X-Token`，白名单路径跳过（`/state/records` 和 `/health/observer` 需认证）
- 限流：Observer ThrottleMiddleware，固定窗口，超限返回 429
- 沙箱：Observer SandboxMiddleware，FS/网络 allowlist 控制
- 重入守卫：Observer ReentrancyGuard，默认最大深度 3
- CORS：可配置，默认允许所有来源

## Postscript: Future Planning & Improvements

- 引入数据库迁移工具（如 `beanie` 或 `mongodb-migrate`）
- 评估是否需要更细粒度的权限控制（RBAC）
- 考虑为高频接口增加缓存层

## Workflow Standardization Review

1. **Repetitive labor identification**: API 路由表在 architecture.md、CLAUDE.md 和 03 设计文档中三处维护。
2. **Decision criteria missing**: 设计决策的"最终确定"vs"临时方案"缺乏标识机制。
3. **Information silos**: 安全约束分散在 security.md 和 03 安全约束章节。
4. **Feedback loop**: 代码接口变更缺乏向设计文档的自动通知。

## System Architecture Evolution Thinking

- **A1. Current architecture bottleneck**: 设计文档为纯文本，缺乏与代码的实时链接。
- **A2. Next natural evolution node**: 引入 Mermaid 架构图（graph TB + sequenceDiagram）使系统可视化。
- **A3. Risks and rollback plans for evolution**: Mermaid 图与代码不同步风险。回退：保持文本为主要权威。
