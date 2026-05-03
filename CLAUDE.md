# CLAUDE.md

> 行为规范见 .claude/shared/behavioral-guidelines.md
> 项目架构约定见 docs/architecture.md

> **重要**：这是 Claude Code 的"长期记忆"和"操作指南"。在执行任何任务前，请先阅读此文件。

## 项目概述

YiAi 是一个基于 FastAPI 的 AI 服务后端，通过 REST API 端点提供 RSS 管理、文件上传、AI 聊天、状态存储、可靠性监控和动态模块执行功能。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python main.py
```

服务器运行在 http://0.0.0.0:8000，已启用自动重载。API 文档可通过 /docs 和 /redoc 访问。

## 关键命令

| 命令 | 用途 |
|---------|---------|
| `python main.py` | 启动开发服务器 |
| `python -m pytest tests/ -v` | 运行所有测试（如果存在测试） |
| `python src/cli/state_query.py list` | 查询状态记录（表格格式） |
| `python src/cli/state_query.py stats` | 查看状态记录统计 |
| `python src/cli/state_query.py export -o out.json` | 导出状态记录为 JSON |

---

## 代码风格与规范

### Python 代码风格

- **代码格式化**：使用 Ruff 进行格式化和 linting
- **命名约定**：
  - 模块/文件：snake_case（如 `chat_service.py`）
  - 类名：CapWords（如 `ChatService`）
  - 函数/方法：snake_case（如 `send_message()`）
  - 常量：UPPER_SNAKE_CASE（如 `MAX_RETRIES`）
- **类型注解**：所有函数参数和返回值都应有类型注解
- **文档字符串**：使用 Google 风格的 docstring

**示例**：
```python
from typing import Optional, List
from pydantic import BaseModel

class Message(BaseModel):
    content: str
    role: str = "user"

class ChatService:
    """AI 聊天服务类"""

    async def send_message(
        self,
        message: Message,
        user_id: Optional[str] = None
    ) -> List[Message]:
        """发送消息到 AI 服务并获取回复

        Args:
            message: 消息对象
            user_id: 可选的用户 ID

        Returns:
            消息列表，包含用户消息和 AI 回复
        """
        pass
```

### Git 提交规范

- 使用现在时态（"Add feature" 而非 "Added feature"）
- 描述要清晰具体
- 格式：`<type>(<scope>): <subject>`
  - type: feat, fix, docs, style, refactor, test, chore

**示例**：
```
feat(chat): add streaming support for AI responses
fix(rss): handle feed parsing errors gracefully
docs: update API documentation for upload endpoints
```

---

## 开发工作流

### 添加新功能

1. **阅读规格**：查看 `specs/features/` 下的功能规格（如果存在）
2. **设计方案**：确认架构设计，必要时更新 `docs/architecture.md`
3. **实现代码**：
   - API 路由：`src/api/routes/`
   - 业务逻辑：`src/services/`
   - 数据模型：`src/models/schemas.py`
4. **测试验证**：确保现有功能不受影响
5. **更新文档**：更新相关文档和 CLAUDE.md（如需要）

### 修复 Bug

1. **理解问题**：确认 bug 的具体表现和影响范围
2. **定位代码**：找到相关代码位置
3. **编写修复**：修复问题并添加注释说明原因
4. **验证修复**：测试确认问题已解决

### 代码审查要点

- 遵循代码风格规范
- 有适当的类型注解和文档字符串
- 没有引入安全漏洞
- 错误处理适当
- 日志记录合理

---

## AI Coding 配置

### 自定义技能

项目特定技能位于 `.claude/skills/` 目录，Claude Code 会自动加载。

### 规格说明

详细的功能规格、API 规格和架构规格位于 `specs/` 目录。

### MCP 服务器

MCP (Model Context Protocol) 服务通过 `fastapi-mcp` 自动将 FastAPI 端点暴露为 MCP 工具。配置位于 `.claude/mcp.json`，生产端点为 `https://api.effiy.cn/mcp`。

18 个 MCP 工具分 5 类：Upload(9)、Execution(2)、WeWork(1)、State(5)、Observer(1)，完整清单见 [docs/mcp-service-optimization/03_design-document.md](docs/mcp-service-optimization/03_design-document.md)，快速入门见 [docs/mcp-service-optimization/04_usage-document.md](docs/mcp-service-optimization/04_usage-document.md)。

### 记忆目录

`.claude/memory/` 目录用于持久化对话记忆，**不提交到 Git**。

---

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
│   │   ├── maintenance.py   # 维护端点
│   │   ├── state.py         # 状态记录 CRUD
│   │   └── observer_health.py # Observer 健康检查
│   ├── core/                 # 核心基础设施
│   │   ├── config.py        # 配置（YAML + 环境变量）
│   │   ├── database.py      # MongoDB 单例
│   │   ├── logger.py        # 日志设置
│   │   ├── exceptions.py    # 自定义异常
│   │   ├── response.py      # 统一响应格式
│   │   ├── middleware.py    # 认证中间件
│   │   ├── exception_handler.py # 异常处理器
│   │   ├── error_codes.py   # 错误码定义
│   │   ├── utils.py         # 工具函数
│   │   └── observer/        # Observer Reliability 组件
│   │       ├── throttle.py  # 请求限流
│   │       ├── sampler.py   # 尾部采样
│   │       ├── sandbox.py   # 沙箱安全
│   │       ├── lazy_start.py # 懒启动
│   │       └── guard.py     # 重入守卫
│   ├── models/               # Pydantic 模型与集合
│   │   ├── schemas.py       # Pydantic 模式
│   │   └── collections.py   # 集合定义
│   ├── services/             # 业务逻辑
│   │   ├── execution/       # 模块执行器
│   │   ├── rss/             # RSS 源管理
│   │   ├── ai/              # Ollama 聊天服务
│   │   ├── storage/         # OSS 存储
│   │   ├── static/          # 静态文件服务
│   │   ├── state/           # 状态存储服务
│   │   └── database/        # 数据访问
│   └── cli/                  # CLI 工具
│       └── state_query.py   # 状态查询 CLI
├── config.yaml             # 配置文件
├── docs/                   # 详细文档目录
└── tests/                  # 测试目录（如果存在）
```

### 关键架构模式

1. **模块执行引擎**：`/execution` 端点允许通过 GET/POST 动态执行任何白名单中的模块方法。支持同步/异步函数、生成器、异步生成器和 SSE 流式传输。

2. **配置系统**：使用 Pydantic Settings，结合 YAML 配置文件（`config.yaml`）+ 环境变量覆盖。嵌套的 YAML 键会被扁平化为蛇形命名（例如，`server.host` → `server_host`）。

3. **数据库**：通过 Motor 异步驱动实现 MongoDB 单例。通过 `core.database.db` 全局实例访问。

4. **生命周期管理**：FastAPI 生命周期在 `src/main.py` 中管理 MongoDB 连接和 RSS 调度器的启动/关闭。

5. **双重存储策略**：文件上传功能支持 OSS 云存储和本地静态存储两种模式，自动 fallback。

6. **MCP 服务器集成**：通过 `fastapi-mcp` 自动将 FastAPI 端点暴露为 Model Context Protocol 服务，`/mcp` 路径由 MCP 服务器接管。

7. **State Store 服务**：结构化状态记录的 CRUD 服务，包含 `StateStoreService`（CRUD）、`SkillRecorder`（fire-and-forget 执行记录）和 `SessionAdapter`（遗留文档转换）。通过 `/state/records` API 和 CLI 工具访问。

8. **Observer Reliability 系统**：5 组件可靠性监控——ThrottleMiddleware（IP 限流）、TailSampler（慢/错误请求采样）、SandboxMiddleware（FS/网络沙箱）、LazyStartManager（懒启动）、ReentrancyGuard（重入守卫）。中间件栈：Auth → CORS → Throttle → Sampler。健康状态通过 `/health/observer` 查询。

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
- `observer.enabled`：启用/禁用 Observer Reliability 系统
- `state_store.enabled`：启用/禁用 State Store 服务

详细的配置说明请参考 [docs/architecture.md](docs/architecture.md)。

## 数据库集合

- `sessions`：用户会话
- `rss`：RSS 文章
- `chat_records`：聊天历史
- `oss_file_info`：文件元数据
- `oss_file_tags`：文件标签
- `pet_data_sync`：宠物数据同步（可选）
- `seeds`：种子数据（可选）
- `state_records`：结构化状态记录（技能执行记录、通用快照等）

详细的数据库集合说明请参考 docs/ 目录下的相关文档。

## API 端点

| 方法 | 路径 | 描述 |
|--------|------|-------------|
| GET/POST | `/execution` | 执行模块方法 |
| POST | `/upload` | 通用文件上传 |
| POST | `/upload-image-to-oss` | 图片上传到 OSS |
| POST | `/read-file` | 读取文件内容 |
| POST | `/write-file` | 写入文件 |
| POST | `/delete-file` | 删除文件 |
| POST | `/delete-folder` | 删除文件夹 |
| POST | `/rename-file` | 重命名文件 |
| POST | `/rename-folder` | 重命名文件夹 |
| POST | `/wework/send-message` | 发送消息到企业微信 |
| POST | `/cleanup-unused-images` | 清理未引用的图片 |
| GET/POST | `/mcp` | MCP 协议端点（由 fastapi-mcp 自动挂载） |
| POST | `/state/records` | 创建状态记录 |
| GET | `/state/records` | 查询状态记录 |
| GET | `/state/records/{key}` | 获取单条状态记录 |
| PUT | `/state/records/{key}` | 更新状态记录 |
| DELETE | `/state/records/{key}` | 删除状态记录 |
| GET | `/health/observer` | Observer 运行时健康检查 |

详细的 API 端点文档请参考 docs/ 目录下的相关文档。

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

## 详细文档

更多详细文档请参考 `docs/` 目录：

- [docs/architecture.md](docs/architecture.md) - 架构设计
- [docs/changelog.md](docs/changelog.md) - 变更日志
- [docs/devops.md](docs/devops.md) - 构建与运维
- [docs/network.md](docs/network.md) - 网络请求约定
- [docs/state-management.md](docs/state-management.md) - 状态管理
- [docs/FAQ.md](docs/FAQ.md) - 常见问题
- [docs/auth.md](docs/auth.md) - 认证鉴权
- [docs/security.md](docs/security.md) - 安全策略
