# YiAi

> FastAPI 驱动的 AI 服务后端，提供网页爬取、RSS 管理、AI 对话、文件上传和动态模块执行能力

## 📁 项目结构说明 (2026-03-10 重构)

本项目已完成结构重构，采用标准 Python `src/layout` 结构：
- 源码位于 `src/yiai/` 目录
- 可通过 `python main.py`（兼容方式）、`python -m yiai` 或 `uvicorn yiai.main:app` 启动
- 详细迁移指南请查看 [docs/migration.md](docs/migration.md)
- 架构文档请查看 [docs/architecture.md](docs/architecture.md)
- 开发指南请查看 [docs/development.md](docs/development.md)

## 核心特性

- ✅ **RSS 管理**：APScheduler 定时轮询，自动解析和存储 RSS 文章
- 🤖 **AI 对话**：Ollama 集成，支持本地 LLM 对话
- 📦 **动态执行**：安全的模块方法动态执行引擎，支持同步/异步/SSE 流式输出
- 📁 **文件上传**：OSS 兼容的文件存储服务
- 💾 **MongoDB 集成**：异步 Motor 驱动，会话、聊天记录、RSS 数据持久化

## 快速开始

### 3步启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置（可选：修改 config.yaml 或使用环境变量）

# 3. 启动服务
python main.py
```

### 访问地址

- **服务地址**: http://localhost:8000
- **API 文档 (Swagger)**: http://localhost:8000/docs
- **API 文档 (ReDoc)**: http://localhost:8000/redoc

## 架构概览

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI ( :8000 )                       │
├─────────────────────────────────────────────────────────────┤
│  API Routes  │  /execution  │  /upload  │  /debug  │ ...  │
├─────────────────────────────────────────────────────────────┤
│  Services    │  Crawler     │  RSS      │  AI Chat │ OSS   │
├─────────────────────────────────────────────────────────────┤
│  Core        │  Settings    │  Database │  Logger  │ ...   │
├─────────────────────────────────────────────────────────────┤
│  Storage     │  MongoDB     │  OSS      │  Static Files    │
└─────────────────────────────────────────────────────────────┘
```

### 目录结构

```
YiAi/
├── main.py                 # 应用入口与生命周期管理
├── config.yaml             # 配置文件
├── requirements.txt        # Python 依赖列表
├── CLAUDE.md               # Claude Code 开发指南
├── api/
│   └── routes/             # API 端点
│       ├── debug.py        # 调试/健康检查端点
│       ├── execution.py    # 动态模块执行端点
│       ├── upload.py       # 文件上传端点
│       ├── wework.py       # 企业微信集成
│       └── maintenance.py  # 维护端点
├── core/                   # 核心基础设施
│   ├── settings.py         # 配置管理 (YAML + 环境变量)
│   ├── database.py         # MongoDB 单例
│   ├── logger.py           # 日志设置
│   ├── exceptions.py       # 自定义异常
│   ├── response.py         # 统一响应格式
│   ├── schemas.py          # Pydantic 模型
│   └── middleware.py       # 中间件
└── services/               # 业务逻辑
    ├── execution/          # 模块执行器
    ├── rss/                # RSS 订阅管理
    ├── ai/                 # Ollama 对话服务
    ├── storage/            # OSS 存储
    ├── static/             # 静态文件服务
    └── database/           # 数据访问
```

## 功能模块详解

### 动态模块执行引擎

通过 `/execution` 端点调用任何白名单模块方法，支持：
- 同步/异步函数
- 生成器函数
- SSE 流式输出
- 白名单控制（配置于 `config.yaml > module.allowlist`）

**使用示例**：

```bash
# 调用模块方法
POST /execution
{
  "module_path": "module.path",
  "function_name": "function_name",
  "parameters": {"key": "value"}
}
```

### RSS 服务

- 定时轮询：默认 3600 秒（可通过 `rss.scheduler_interval` 配置）
- 自动解析 Feed 并存储到 MongoDB
- 启动时自动初始化（可通过 `startup.init_rss_system` 配置）

### AI 对话服务

- Ollama 本地 LLM 集成
- 配置：`ollama.url` 和 `ollama.auth`

### 文件上传服务

- OSS 兼容的对象存储
- 支持的文件类型：jpg, jpeg, png, gif, pdf, doc, docx, epub, md
- 最大文件大小：50MB（可配置）

## API 端点摘要

| 方法 | 路径 | 描述 |
|------|------|------|
| GET/POST | `/execution` | 执行模块方法 |
| POST | `/upload` | 上传文件 |
| GET | `/debug/info` | 系统信息 |
| GET | `/debug/health` | 健康检查 |

> **完整 API 文档**：启动服务后访问 `/docs` (Swagger UI) 或 `/redoc`

## 配置说明

### 主要配置文件

**`config.yaml`** - 主配置文件

### 关键配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `server.host` | 服务监听地址 | `0.0.0.0` |
| `server.port` | 服务监听端口 | `8000` |
| `server.reload` | 开发模式自动重载 | `true` |
| `mongodb.url` | MongoDB 连接字符串 | `mongodb://localhost:27017` |
| `mongodb.db_name` | 数据库名称 | `ruiyi` |
| `module.allowlist` | 模块执行白名单 | `["*"]` (允许所有) |
| `rss.scheduler_interval` | RSS 轮询间隔（秒） | `3600` |
| `static.base_dir` | 静态文件目录 | `/var/www/YiKnowledge/static` |
| `middleware.auth_enabled` | 是否启用认证 | `true` |
| `ollama.url` | Ollama 服务地址 | `http://localhost:11434` |

### 环境变量覆盖

支持通过环境变量覆盖配置，格式为**大写+下划线**，例如：

```bash
export MONGODB_URL="mongodb://localhost:27017/mydb"
export SERVER_PORT=8080
export MIDDLEWARE_AUTH_ENABLED=false
```

嵌套配置通过下划线连接，例如 `server.host` → `SERVER_HOST`

## 常见问题

**Q: 如何启用/禁用认证？**
A: 修改 `config.yaml` 中的 `middleware.auth_enabled` 为 `true` 或 `false`

**Q: 在哪里可以找到更详细的开发文档？**
A: 查看项目根目录的 `CLAUDE.md` 获取完整的开发指南

**Q: 如何添加新的 RSS 订阅源？**
A: 使用 `scripts/rss_manager.py` 工具：
   ```bash
   python scripts/rss_manager.py --add <feed_url>
   python scripts/rss_manager.py --list
   ```

---

## 相关项目

Yi-series 系列项目：

- [YiWeb](../YiWeb/)：AI 代码审查前端与共享 CDN 组件库
- [YiH5](../YiH5/)：移动端 AI 助手
- [YiKnowledge](../YiKnowledge/)：文档中心与知识库

---

## 许可证

本项目为 Yi-series 系列的一部分。
