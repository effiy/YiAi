# MCP 服务 — 使用指南与快速入门

> **Document Version**: v1.0 | **Last Updated**: 2026-05-03 | **Maintainer**: Claude Opus 4.7 | **Tool**: Claude Code
>
> **Related Documents**: [Requirement Document](./01_requirement-document.md) | [Requirement Tasks](./02_requirement-tasks.md) | [Design Document](./03_design-document.md) | [Dynamic Checklist](./05_dynamic-checklist.md) | [Project Report](./07_project-report.md) | [CLAUDE.md](../../CLAUDE.md)
>
> **Git Branch**: main
>
> **Doc Start Time**: 14:40:00 | **Doc Last Update Time**: 14:40:00

[Feature Introduction](#feature-introduction) | [Quick Start](#quick-start) | [Operation Scenarios](#operation-scenarios) | [FAQ](#faq) | [Tips](#tips) | [Appendix](#appendix)

---

## Feature Introduction

YiAi MCP 服务通过 Model Context Protocol 将 FastAPI 后端能力暴露给 AI 客户端（如 Claude Desktop、Cursor）。AI 客户端可直接调用文件上传、模块执行、企业微信消息发送、状态记录管理等 18+ 个工具，无需编写 API 调用代码。

**核心能力**：
- 自动发现：客户端连接后自动获取全部工具列表和参数 schema
- 零认证：MCP 端点 `/mcp*` 免 Token 访问（依赖服务端 IP 白名单保护）
- 流式传输：基于 SSE 的实时双向通信
- 分类管理：Upload、Execution、WeWork、State、Observer 五大类工具

---

## Quick Start

### 1. Claude Desktop 配置（推荐）

打开 Claude Desktop 设置文件：
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

添加以下配置：

```json
{
  "mcpServers": {
    "effiy-api": {
      "command": "npx",
      "args": ["-y", "mcp-proxy", "https://api.effiy.cn/mcp"]
    }
  }
}
```

重启 Claude Desktop，在对话中输入 "列出可用的工具"，Claude 将展示 YiAi MCP 全部工具。

### 2. 命令行验证

```bash
# 测试 MCP 端点可达性
curl -X GET https://api.effiy.cn/mcp -H "Accept: text/event-stream" -v

# 使用 mcp-proxy 连接测试（需要 Node.js）
npx -y mcp-proxy https://api.effiy.cn/mcp --list-tools
```

### 3. 第一个工具调用

在 Claude Desktop 中尝试以下对话：

> "帮我创建一个状态记录，key 为 test-mcp，value 为 {status: ok}"

Claude 将自动调用 `create_state_record` 工具完成操作。

### 4. Cursor 配置

```json
{
  "mcpServers": {
    "effiy-api": {
      "url": "https://api.effiy.cn/mcp"
    }
  }
}
```

---

## Operation Scenarios

### 正例：典型使用场景

#### Scenario 1: 文件上传与管理

> **场景**: 用户需要通过 AI 客户端上传文件到 OSS 或本地存储。

**操作步骤**:
1. 在对话中描述上传需求："请把这张图片上传到 OSS，文件名为 logo.png"
2. Claude 自动调用 `upload_image_to_oss` 工具
3. 返回 OSS URL，用户可直接引用

**关键工具**: `upload_file`, `upload_image_to_oss`, `read_file`, `write_file`, `delete_file`

#### Scenario 2: 状态记录管理

> **场景**: 用户需要存储和查询结构化状态数据。

**操作步骤**:
1. 创建记录："创建一个状态记录，key 为 daily-summary，value 包含今天的总结"
2. 查询记录："列出所有带 summary 标签的状态记录"
3. 更新记录："更新 daily-summary 的状态"
4. 删除记录："删除 key 为 old-data 的状态记录"

**关键工具**: `create_state_record`, `query_state_records`, `get_state_record`, `update_state_record`, `delete_state_record`

#### Scenario 3: 企业微信消息发送

> **场景**: 用户需要通过 AI 发送企业微信通知。

**操作步骤**:
1. 描述消息："发送一条企业微信消息，内容为：部署完成，版本 v2.1.0"
2. Claude 调用 `send_wework_message` 工具
3. 返回发送结果

**关键工具**: `send_wework_message`

#### Scenario 4: Observer 健康检查

> **场景**: 运维人员需要检查 Observer 可靠性组件的运行状态。

**操作步骤**:
1. 在对话中输入"检查 Observer 健康状态"
2. Claude 调用 `get_observer_health` 工具
3. 返回各组件的实时指标（限流命中率、采样率、沙箱状态等）

**关键工具**: `get_observer_health`

#### Scenario 5: 动态模块执行

> **场景**: 高级用户需要通过 AI 执行白名单中的模块方法。

**操作步骤**:
1. 描述执行需求："执行 data_processor 模块的 aggregate 方法"
2. Claude 调用 `execute_module_post` 工具
3. 返回执行结果（同步、异步、流式均支持）

**关键工具**: `execute_module_get`, `execute_module_post`

### 反例：常见错误用法

#### Anti-Pattern 1: 尝试调用维护端点

> ❌ "清理一下未使用的图片"

`cleanup_unused_images` 被标记为 `Maintenance` 标签，已从 MCP 排除。应通过 API 或其他管理工具触发。

#### Anti-Pattern 2: 传递错误的参数格式

> ❌ 调用 `create_state_record` 时传入 `parameters={"records": {...}}` 而非直接的 record 字段

MCP 工具的参数 schema 由 Pydantic 模型定义。参数名和类型必须匹配。使用 `query_state_records` 可查看已有记录的字段格式。

#### Anti-Pattern 3: 频繁调用导致限流

> ❌ 在短时间内重复调用同一工具超过限流阈值

Observer 的 TokenBucket 机制对工具调用实施频率限制（默认 100 req/s per category）。超频请求将被拒绝并返回 429。

---

## FAQ

### Q1: 连接 MCP 后看不到工具列表？

**检查清单**：
1. 确认 `https://api.effiy.cn` 可访问：`curl -I https://api.effiy.cn/mcp`
2. 确认 Claude Desktop 版本 >= 0.7.0（支持 MCP）
3. 重启 Claude Desktop 后查看日志（Developer → MCP Logs）
4. 确认 `npx` 可用：`npx --version` (Node.js >= 18)

### Q2: MCP 工具调用返回错误？

通常原因是参数格式不匹配。在 Claude Desktop 中可以让 AI 重新检查参数，或查看工具描述中的 `inputSchema`。

### Q3: MCP 是否需要认证？

不需要。`/mcp*` 路径在 Auth 中间件中已白名单化（见 `src/core/middleware.py:68`）。安全依赖服务端的网络层 IP 白名单和 Observer 限流保护。

### Q4: 如何知道哪些端点可通过 MCP 调用？

所有非 `Maintenance` 标签的端点自动暴露。完整清单见 `03_design-document.md` 的 MCP 工具清单表。排除的端点：`/cleanup-unused-images` 及其备用路径。

### Q5: MCP 工具名会变化吗？

显式设置了 `operation_id` 的工具名保持稳定。如果 `fastapi-mcp` 库升级导致生成规则变化，有 `operation_id` 的工具不受影响。这也是本次优化补全所有 `operation_id` 的原因。

### Q6: 本地开发环境如何配置 MCP？

将 `claude_desktop_config.json` 中的 URL 改为本地地址：

```json
{
  "mcpServers": {
    "effiy-api-local": {
      "command": "npx",
      "args": ["-y", "mcp-proxy", "http://localhost:8000/mcp"]
    }
  }
}
```

### Q7: 如何安全地使用 module.allowlist: ["*"] 的 MCP？

当前 `config.yaml` 中 `module.allowlist: ["*"]` 允许 MCP 调用任意模块方法。建议：
1. 通过 IP 白名单限制 MCP 端点访问来源
2. 定期审计 MCP 调用日志
3. 评估收紧 allowlist 为显式模块列表

---

## Tips

1. **首次使用推荐工具**: `query_state_records` — 无参数，返回已有记录列表，是验证 MCP 连通性最安全的方式
2. **工具描述即文档**: 每个 MCP 工具的 `description` 字段包含参数说明，遇到参数不确定时可让 AI 先查看工具描述
3. **批量操作**: State 记录的 CRUD 支持批量查询和分页（通过 `limit`、`offset` 参数）
4. **安全性**: MCP 工具调用等同于 HTTP API 调用，不要通过 MCP 在公开对话中操作敏感数据
5. **Observer 保护**: MCP 工具调用受 Observer 可靠性组件保护（限流、采样、沙箱），异常调用会被自动采样记录

---

## Appendix

### A. MCP 工具快速参考卡

| 分类 | 工具 | 功能 |
|------|------|------|
| **State** | `create_state_record` | 创建状态记录 |
| | `query_state_records` | 查询状态记录（支持标签筛选和分页） |
| | `get_state_record` | 获取单条状态记录 |
| | `update_state_record` | 更新状态记录 |
| | `delete_state_record` | 删除状态记录 |
| **Upload** | `upload_file` | 通用文件上传 |
| | `upload_image_to_oss` | 图片上传到 OSS |
| | `upload_image_to_oss_alt` | 备用 OSS 上传路径 |
| | `read_file` | 读取文件内容 |
| | `write_file` | 写入文件 |
| | `delete_file` | 删除文件 |
| | `delete_folder` | 删除文件夹 |
| | `rename_file` | 重命名文件 |
| | `rename_folder` | 重命名文件夹 |
| **Execution** | `execute_module_get` | 执行模块方法（GET） |
| | `execute_module_post` | 执行模块方法（POST） |
| **WeWork** | `send_wework_message` | 发送企业微信消息 |
| **Observer** | `get_observer_health` | 查询 Observer 健康状态 |

### B. 客户端兼容性

| 客户端 | 最低版本 | 配置方式 | 备注 |
|--------|---------|---------|------|
| Claude Desktop | 0.7.0+ | 编辑 `claude_desktop_config.json` | 推荐 |
| Cursor | 0.40.0+ | 编辑 MCP 设置 | 需 URL 格式 |
| Claude Code CLI | 最新版 | 编辑 `.claude/mcp.json` | 已内置配置 |
| Observer Client | — | `node observer-client.js` | 程序化接入 |

### C. 安全模型

```text
Internet → TLS → api.effiy.cn /mcp
                    │
                    ├── Auth: /mcp* whitelisted (no token)
                    ├── Throttle: IP-level rate limiting
                    ├── Sampler: tail sampling for slow/error requests
                    └── MCP: FastApiMCP auto-resolve tools
```

**风险提示**: MCP 端点无认证暴露。依赖网络层 IP 白名单保护。如果服务面向公网，建议在反向代理层（Nginx）增加 IP 限制。

## Postscript: Future Planning & Improvements

- 增加工具调用示例库（每个工具的典型 prompt 示例）
- 考虑增加 MCP 工具调用的使用统计分析
- 计划提供交互式 MCP 工具浏览器（Web UI）

## Workflow Standardization Review
1. **Repetitive labor identification**: 工具参考卡与 03 工具清单表内容重复，可统一为单一来源
2. **Decision criteria missing**: FAQ 条目选择标准不明确（哪些问题值得收录）
3. **Information silos**: Observer 客户端的详细配置分散在 observer skill 文档中
4. **Feedback loop**: 缺少用户反馈渠道（哪些 FAQ 最常被查阅、哪些工具最常遇到问题）

## System Architecture Evolution Thinking
- **A1. Current architecture bottleneck**: 使用指南为静态文档，无法反映工具实时状态
- **A2. Next natural evolution node**: 动态 MCP 工具浏览器 → 从 `/openapi.json` 实时生成交互式 API 文档
- **A3. Risks and rollback plans for evolution**: 动态文档依赖 OpenAPI schema 准确性，需持续校验 schema → tool name 一致性
