# MCP 服务优化与补充

> **Document Version**: v1.0 | **Last Updated**: 2026-05-03 | **Maintainer**: Claude Opus 4.7 | **Tool**: Claude Code
>
> **Related Documents**: [Requirement Tasks](./02_requirement-tasks.md) | [Design Document](./03_design-document.md) | [Usage Document](./04_usage-document.md) | [CLAUDE.md](../../CLAUDE.md)
>
> **Git Branch**: main
>
> **Doc Start Time**: 14:30:00 | **Doc Last Update Time**: 14:30:00

[Feature Overview](#feature-overview) | [User Stories](#user-stories) | [Acceptance Criteria](#acceptance-criteria) | [Feature Details](#feature-details)

---

## Feature Overview

YiAi 已通过 `fastapi-mcp` 库将 FastAPI 端点自动暴露为 MCP（Model Context Protocol）工具，外部 AI 客户端可通过 `https://api.effiy.cn/mcp` 调用。当前 MCP 服务功能可用但存在以下不足：工具描述缺乏中文引导、部分端点 `operation_id` 缺失导致工具名可读性差、无快速入门指南、用户难以了解全部可用工具。本次优化目标为：补全工具元数据以提升功能触达率、输出中文快速入门指南降低使用门槛、建立 MCP 工具清单文档供用户查阅。

**Core Values**
- 提升 MCP 工具可发现性（补全 operation_id 和描述信息）
- 降低新用户上手成本（提供复制即用的快速入门指南）
- 建立可持续维护的 MCP 文档体系

---

## User Stories and Feature Requirements

**Priority icons**: P0 - must have | P1 - should have | P2 - nice to have

| User Story | Acceptance Criteria | Process-Generated Documents | Output Smart Documents |
|------------|---------------------|----------------------------|------------------------|
| P0 As an AI agent developer, I want clear MCP tool names and descriptions, so that I can discover and call the right tools without reading source code<br/><br/>**Main Operation Scenarios**:<br/>- Browse available MCP tools in Claude Desktop and understand each tool's purpose<br/>- Call an MCP tool with correct parameters based on its description<br/>- Identify which endpoints are NOT available via MCP and why | 1. All MCP-exposed endpoints have explicit `operation_id` (snake_case, English, verb_noun)<br/>2. All MCP-exposed endpoints have `summary` and `description` fields<br/>3. Excluded endpoints (Maintenance tag) are documented with rationale | [Requirement Tasks](./02_requirement-tasks.md)<br/>[Design Document](./03_design-document.md)<br/>[Project Report](./07_project-report.md) | [Generate Document Skill](../../.claude/skills/generate-document/SKILL.md)<br/>[Requirement Document Specification](../../.claude/skills/generate-document/rules/requirement-document.md)<br/>[Requirement Document Template](../../.claude/skills/generate-document/templates/requirement-document.md)<br/>[Requirement Document Checklist](../../.claude/skills/generate-document/checklists/requirement-document.md) |
| P1 As a new YiAi user, I want a quick start guide, so that I can connect Claude Desktop to YiAi MCP within 2 minutes<br/><br/>**Main Operation Scenarios**:<br/>- Copy a JSON config snippet into Claude Desktop settings<br/>- Verify the MCP connection is working<br/>- Call a sample tool (e.g., list state records) to confirm functionality | 1. Quick start guide includes copy-paste-ready `claude_desktop_config.json` snippet<br/>2. Guide includes verification steps with expected output<br/>3. Guide covers both Claude Desktop and programmatic (Node.js) access | [Requirement Tasks](./02_requirement-tasks.md)<br/>[Design Document](./03_design-document.md)<br/>[Project Report](./07_project-report.md) | [Usage Document](../../.claude/skills/generate-document/rules/usage-document.md)<br/>[Usage Document Checklist](../../.claude/skills/generate-document/checklists/usage-document.md) |
| P2 As a YiAi maintainer, I want a complete MCP tool inventory with descriptions, so that I can audit tool quality and identify gaps<br/><br/>**Main Operation Scenarios**:<br/>- Browse all MCP tools grouped by category (Upload, Execution, WeWork, State, Observer)<br/>- See each tool's parameters, response format, and auth requirements<br/>- Identify tools with missing or unclear descriptions | 1. Tool inventory covers all 18+ MCP-exposed endpoints<br/>2. Each tool entry includes: name, HTTP method, path, parameters, response, auth requirement<br/>3. Tool descriptions verified against actual route handler code | [Requirement Tasks](./02_requirement-tasks.md)<br/>[Design Document](./03_design-document.md)<br/>[Project Report](./07_project-report.md) | [Dynamic Checklist](../../.claude/skills/generate-document/rules/dynamic-checklist.md)<br/>[Dynamic Checklist Checklist](../../.claude/skills/generate-document/checklists/dynamic-checklist.md) |

---

## Document Spec

- **One numbered set per user story**
- **Anti-hallucination**: uncertain content write `> TBD (reason: …)`

---

## Feature Details

### MCP 工具元数据补全

- **Description**: 为所有 MCP 暴露的 FastAPI 端点显式设置 `operation_id`（英文 snake_case，动词_名词格式），确保 `fastapi-mcp` 生成的工具名可读且稳定。为缺失 `summary`/`description` 的端点补充中文描述，使 AI 客户端能理解工具用途和参数含义。
- **Boundaries and Exceptions**: 排除 `Maintenance` 标签的端点不暴露（`/cleanup-unused-images`），`/mcp` 端点本身由 `fastapi-mcp` 接管。`operation_id` 变更需同步更新所有引用文档和 Observer fallback 映射表。
- **Value/Motivation**: 当前 State 路由的 5 个端点和 Observer Health 端点无 `operation_id`，`fastapi-mcp` 自动生成的工具名不可控（如 `api_v1_state_records_post`），用户难以理解。补全后工具名如 `create_state_record` 一目了然。

### 快速入门指南

- **Description**: 在 `04_usage-document.md` 中提供自包含的快速入门指南，包含：Claude Desktop MCP 配置 JSON 片段（可直接复制粘贴）、验证连接的命令、第一个工具调用示例、常见问题排查步骤。
- **Boundaries and Exceptions**: 指南假设用户已能访问 `https://api.effiy.cn`。不涵盖本地开发环境搭建（由 `docs/devops.md` 覆盖）。指南中的工具名称基于补全后的 `operation_id`。
- **Value/Motivation**: 当前无任何 MCP 用户文档，新用户只能通过阅读源码了解 MCP 服务。快速入门指南可将首次连接时间从数小时缩短到 2 分钟。

### MCP 工具清单

- **Description**: 建立完整的 MCP 工具清单，按功能分类列出所有 18+ 个暴露端点，每项包含工具名、HTTP 方法、路径、参数说明、响应格式、是否需要认证。
- **Boundaries and Exceptions**: 工具清单基于代码实际状态生成，非手工维护。清单同步标注已知风险（如 `module.allowlist: ["*"]` 的安全影响）。
- **Value/Motivation**: 提供单一可信来源，用户和 AI 客户端可快速了解 YiAi MCP 的完整能力边界。

### MCP 架构文档更新

- **Description**: 更新 `docs/architecture.md` 第 6 节，补充 MCP 请求生命周期说明、工具命名规则、安全模型（无认证 + IP 白名单依赖）、与 Observer 可靠性组件的交互关系。
- **Boundaries and Exceptions**: 不修改 `docs/architecture.md` 其他章节。更新内容与 `docs/mcp-service-optimization/` 文档集保持交叉引用。
- **Value/Motivation**: 当前架构文档 MCP 部分仅 15 行代码片段，缺少运行机制和安全模型说明。

---

## Acceptance Criteria

### P0 - Must Pass
- [ ] **MCP 工具元数据**: 所有 MCP 暴露端点具有显式 `operation_id`，格式为英文 snake_case 动词_名词
- [ ] **快速入门指南可执行**: 新用户按照 `04_usage-document.md` 的快速入门步骤，能在 2 分钟内完成 Claude Desktop MCP 连接配置
- [ ] **工具清单完整**: `03_design-document.md` 包含全部 18+ MCP 工具的分类清单，每项含名称、路径、参数、响应描述
- [ ] **架构文档更新**: `docs/architecture.md` 第 6 节包含 MCP 请求生命周期和工具命名规则

### P1 - Should Pass
- [ ] **工具描述可读性**: 每个 MCP 工具的 `description` 字段包含至少一句中文功能说明
- [ ] **文档交叉引用**: `docs/mcp-service-optimization/` 与 `docs/architecture.md`、`CLAUDE.md` 之间建立双向链接
- [ ] **安全风险标注**: 工具清单中标注 `module.allowlist: ["*"]` 和 MCP 无认证的安全风险

### P2 - Nice to Have
- [ ] **MCP 连通性测试**: 提供基本的 MCP 端点健康检查方法
- [ ] **多语言示例**: 快速入门包含 Node.js (Observer Client) 和 Python 两种接入方式

---

## Usage Scenario Examples

### Scenarios

#### Scenario 1: AI Agent 开发者首次接入 YiAi MCP

> **Background**: 开发者希望在 Claude Desktop 中使用 YiAi MCP 工具来管理文件、查询状态记录。
>
> **Operation**: 打开 `04_usage-document.md` → 复制 `claude_desktop_config.json` 片段 → 粘贴到 Claude Desktop 设置 → 重启 Claude Desktop → 在对话中输入"列出可用的 YiAi 工具" → Claude 展示工具列表。
>
> **Result**: 开发者能在 2 分钟内看到完整的 YiAi MCP 工具列表，并成功调用第一个工具。

#### Scenario 2: 运维人员审计 MCP 工具安全性

> **Background**: 安全团队需要了解通过 MCP 暴露了哪些能力、是否存在越权风险。
>
> **Operation**: 打开 `03_design-document.md` → 查阅 MCP 工具清单表 → 确认无认证访问的端点范围 → 确认 `Maintenance` 标签端点已排除 → 查阅安全风险标注。
>
> **Result**: 运维人员获得完整的 MCP 工具安全画像，能评估风险并制定访问控制策略。

## Postscript: Future Planning & Improvements

- 考虑为 MCP 服务增加服务端速率限制（当前仅 Observer 客户端有限流）
- 评估 `module.allowlist` 从 `["*"]` 收紧为显式模块列表的可行性
- 探索 MCP 工具使用统计和日志分析能力

## Workflow Standardization Review
1. **Repetitive labor identification**: MCP 工具清单的手工维护与代码同步是潜在重复劳动，可考虑从 OpenAPI schema 自动生成工具清单
2. **Decision criteria missing**: module.allowlist 收紧决策缺乏数据支撑（哪些模块实际被 MCP 调用过）
3. **Information silos**: MCP fallback 策略在 `.claude/shared/mcp-fallback-contract.md`，工具清单在 `docs/mcp-service-optimization/`，用户需要跨文件查阅
4. **Feedback loop**: 缺少 MCP 工具使用反馈机制（哪些工具常用、哪些从未调用、哪些描述不清晰）

## System Architecture Evolution Thinking
- **A1. Current architecture bottleneck**: MCP 工具名和描述依赖代码注解质量，无自动化校验机制（如 CI 检查 `operation_id` 覆盖率）
- **A2. Next natural evolution node**: 从代码注解自动生成 MCP 工具文档 → OpenAPI schema → MCP tool manifest 的自动化管道
- **A3. Risks and rollback plans for evolution**: `operation_id` 变更可能影响已集成的 MCP 客户端（工具名变化导致调用失败），需在变更前通知所有已知客户端，并在文档中标注 breaking changes
