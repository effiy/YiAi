# 项目初始化需求文档

> 本文档描述 YiAi 项目初始化的背景、目标与范围。

---

## 1. 项目背景

YiAi 是一个基于 FastAPI 的 AI 服务后端，旨在通过 REST API 提供 RSS 管理、文件上传、AI 聊天和动态模块执行等功能。项目采用模块化设计，支持动态扩展，便于快速迭代和集成新的 AI 能力。

## 2. 项目目标

- 提供稳定、可扩展的 AI 服务后端
- 支持多种 AI 模型集成（以 Ollama 为主）
- 实现动态模块执行，允许通过 API 灵活调用业务逻辑
- 提供完整的文件上传与管理能力（OSS + 本地双存储）
- 集成 RSS 源自动抓取与管理
- 支持企业微信消息推送
- 提供结构化状态记录的 CRUD 服务（State Store）
- 提供请求限流、尾部采样、执行沙箱等可靠性监控（Observer Reliability）
- 提供 CLI 工具用于状态数据查询和导出

## 3. 技术约束

- Python >= 3.10
- MongoDB >= 5.0 作为持久化存储
- FastAPI + Uvicorn 作为 Web 服务框架
- 异步优先（Motor、aiohttp、asyncio）
- 配置通过 YAML + 环境变量管理

## 4. 非功能需求

- **可维护性**：清晰的目录结构，遵循单一职责原则
- **可测试性**：应用工厂模式支持不同环境的测试配置
- **安全性**：可选的令牌认证，白名单机制，路径安全校验
- **可靠性**：Observer 系统提供限流、采样、沙箱、重入守卫多层防护
- **可观测性**：Observer 健康端点和采样机制，统一的日志格式和错误响应

## 5. 关键依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| fastapi | >=0.104.0 | Web 框架 |
| uvicorn | >=0.24.0 | ASGI 服务器 |
| pydantic | >=2.0.0 | 数据验证 |
| motor | >=3.3.0 | MongoDB 异步驱动 |
| ollama | >=0.1.0 | AI 聊天客户端 |
| fastapi-mcp | >=0.4.0 | MCP 协议服务 |
| oss2 | >=2.18.0 | 阿里云 OSS |
| apscheduler | >=3.10.0 | 定时任务调度 |
| typer | >=0.9.0 | CLI 工具框架 |
| rich | >=13.0.0 | CLI 终端美化 |
| tenacity | >=8.2.3 | 重试机制（预留） |

## Postscript: Future Planning & Improvements

- 考虑引入依赖安全扫描工具（如 `safety` 或 `pip-audit`）
- 评估多实例部署方案（Redis 外部化 session）
- 完善自动化测试覆盖

## Workflow Standardization Review

1. **Repetitive labor identification**: 需求文档中的依赖表与 requirements.txt 手动同步，可自动化。
2. **Decision criteria missing**: 何时将依赖标记为"关键依赖"缺乏标准。
3. **Information silos**: 技术约束信息在 CLAUDE.md 和 01 需求文档中分散维护。
4. **Feedback loop**: 需求与实际代码功能的差异缺乏自动检测。

## System Architecture Evolution Thinking

- **A1. Current architecture bottleneck**: 需求与实现的追溯链为纯文本，无法自动化验证。
- **A2. Next natural evolution node**: 引入需求追溯矩阵，将需求条目链接到具体 API 端点。
- **A3. Risks and rollback plans for evolution**: 过度自动化追溯可能增加维护成本。回退：保持文本为主。
