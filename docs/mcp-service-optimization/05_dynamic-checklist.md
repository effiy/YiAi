# MCP 服务优化 — 动态检查清单

> **Document Version**: v1.0 | **Last Updated**: 2026-05-03 | **Maintainer**: Claude Opus 4.7 | **Tool**: Claude Code
>
> **Related Documents**: [Requirement Tasks](./02_requirement-tasks.md) | [Design Document](./03_design-document.md) | [Usage Document](./04_usage-document.md) | [CLAUDE.md](../../CLAUDE.md)
>
> **Git Branch**: main
>
> **Doc Start Time**: 14:45:00 | **Doc Last Update Time**: 14:45:00

[General Checks](#general-checks) | [Scenario Verification](#scenario-verification) | [Feature Implementation](#feature-implementation) | [Code Quality](#code-quality) | [Testing](#testing) | [Check Summary](#check-summary)

---

## General Checks

### P0 — 阻塞项

- [ ] **G1 文档完整性**: `docs/mcp-service-optimization/` 目录包含全部 6 个文档（01-05, 07）
- [ ] **G2 文档可读**: 所有 Markdown 文件无渲染错误，链接有效，表格对齐
- [ ] **G3 交叉引用**: 文档间链接（01↔02↔03↔04↔05↔07）全部有效，无 404
- [ ] **G4 外部引用**: 指向 `docs/architecture.md`、`CLAUDE.md`、`docs/auth.md` 的链接有效
- [ ] **G5 代码锚点**: 文档中引用的代码位置（文件:行号）与实际代码一致
- [ ] **G6 版本一致性**: 所有文档的 `Document Version` 和 `Last Updated` 一致

### P1 — 应通过

- [ ] **G7 中文表达**: 文档内容以中文为主，专业术语首次出现时有英文对照
- [ ] **G8 Mermaid 图表**: 03_design-document.md 和 02_requirement-tasks.md 中的 Mermaid 图表语法正确，可渲染
- [ ] **G9 表格可读**: 所有表格列对齐，内容不溢出，移动端可读

### P2 — 建议通过

- [ ] **G10 术语一致性**: 全文档集中 MCP、operation_id、FastApiMCP 等术语使用一致
- [ ] **G11 代码块语言标注**: 所有代码块标注了正确的语言标识（json, python, bash, mermaid）

---

## Scenario Verification

### P0 — 阻塞项

- [ ] **S1 快速入门验证**: 按 `04_usage-document.md` 的 Quick Start 步骤操作：
  - [ ] S1.1 `claude_desktop_config.json` JSON 格式有效
  - [ ] S1.2 `curl` 验证命令语法正确
  - [ ] S1.3 `npx mcp-proxy` 命令可用（前提：Node.js >= 18）
- [ ] **S2 工具清单完整性**: `03_design-document.md` 中的工具清单表：
  - [ ] S2.1 Upload 类 9 个工具全部列出
  - [ ] S2.2 Execution 类 2 个工具全部列出
  - [ ] S2.3 WeWork 类 1 个工具列出
  - [ ] S2.4 State 类 5 个工具全部列出
  - [ ] S2.5 Observer 类 1 个工具列出
  - [ ] S2.6 Maintenance 排除端点列出并注明原因
- [ ] **S3 operation_id 补全**: 所有需要补全 operation_id 的端点已在文档中明确列出：
  - [ ] S3.1 State 路由 5 个 operation_id 已记录
  - [ ] S3.2 Observer Health 路由 operation_id 已记录

### P1 — 应通过

- [ ] **S4 工具描述可读性**: 每个 MCP 工具的 `description` 或文档描述包含至少一句中文说明
- [ ] **S5 参数文档**: 每个工具在工具清单中标注了参数类型和必填/可选
- [ ] **S6 反例覆盖**: `04_usage-document.md` 包含至少 2 个常见错误用法及纠正方式

### P2 — 建议通过

- [ ] **S7 多客户端验证**: 快速入门指南覆盖 Claude Desktop 和 Cursor 两种客户端
- [ ] **S8 Python 示例**: 附录中包含 Python 客户端接入示例

---

## Feature Implementation

### P0 — 阻塞项

- [ ] **F1 State 路由 operation_id**: `src/api/routes/state.py` 中 5 个端点全部添加 `operation_id` 参数
  - [ ] F1.1 `POST /state/records` → `operation_id="create_state_record"`
  - [ ] F1.2 `GET /state/records` → `operation_id="query_state_records"`
  - [ ] F1.3 `GET /state/records/{key}` → `operation_id="get_state_record"`
  - [ ] F1.4 `PUT /state/records/{key}` → `operation_id="update_state_record"`
  - [ ] F1.5 `DELETE /state/records/{key}` → `operation_id="delete_state_record"`
- [ ] **F2 Observer Health operation_id**: `src/api/routes/observer_health.py` 添加 `operation_id="get_observer_health"`
- [ ] **F3 命名格式**: 所有新增 `operation_id` 使用 `snake_case`，动词_名词格式，英文小写

### P1 — 应通过

- [ ] **F4 架构文档更新**: `docs/architecture.md` 第 6 节补充 MCP 请求生命周期说明
- [ ] **F5 CLAUDE.md 更新**: 架构模式 6 补充 MCP 工具清单入口链接
- [ ] **F6 Upload Schema 增强**: `FileUploadRequest` 和 `ImageUploadToOssRequest` 的 `Field` 描述增强
- [ ] **F7 MCP 中间件验证**: 验证 `FastApiMCP.mount()` 是否绕过 HTTP 中间件栈

### P2 — 建议通过

- [ ] **F8 alt 路由评估**: `upload_image_to_oss_alt` 的去留决策记录在文档中
- [ ] **F9 安全文档更新**: `docs/auth.md` 和 `docs/network.md` 补充 MCP 安全模型说明
- [ ] **F10 连通性测试**: 添加基本的 MCP 端点健康检查测试

---

## Code Quality

### P0 — 阻塞项

- [ ] **C1 无破坏性变更**: operation_id 添加不影响现有 HTTP API 行为
- [ ] **C2 命名无冲突**: 新增 operation_id 不与已有 operation_id 重复

### P1 — 应通过

- [ ] **C3 代码风格**: 变更代码通过 Ruff 格式化和 lint 检查
- [ ] **C4 import 无冗余**: 代码变更不引入未使用的 import

### P2 — 建议通过

- [ ] **C5 类型注解**: 变更涉及的文件中函数参数和返回值有类型注解
- [ ] **C6 无新增 TODO/FIXME**: 代码变更不引入未解决的 TODO 或 FIXME 注释

---

## Testing

### P0 — 阻塞项

- [ ] **T1 服务器启动**: `python main.py` 启动后，`/mcp` 端点可访问
- [ ] **T2 工具列表**: 启动后 MCP `tools/list` 返回的工具列表包含所有新 operation_id
- [ ] **T3 工具调用**: 通过 MCP 调用 `query_state_records`（或等同工具）返回正确结果

### P1 — 应通过

- [ ] **T4 SSE 连接稳定性**: MCP SSE 连接在 5 分钟内无异常断开
- [ ] **T5 认证绕行**: `/mcp` 路径在无 X-Token 情况下可正常访问
- [ ] **T6 排除端点**: `Maintenance` 标签端点不在 MCP 工具列表中

### P2 — 建议通过

- [ ] **T7 并发工具调用**: 同时调用 3 个不同 MCP 工具不报错
- [ ] **T8 错误响应**: 传递无效参数时 MCP 返回可读的错误信息而非 500

---

## Check Summary

### 统计

| 优先级 | 总数 | 预期通过 | 实际状态 |
|--------|------|---------|---------|
| P0 | 17 | 17 | 待验证 |
| P1 | 14 | 14 | 待验证 |
| P2 | 8 | 8 | 待验证 |
| **合计** | **39** | **39** | **待验证** |

### 关键阻塞项（P0 不通过则不可发布）

1. **G1-G6**: 文档完整性和交叉引用
2. **S1-S3**: 快速入门可执行性和工具清单完整性
3. **F1-F3**: State 和 Observer 路由 operation_id 补全
4. **C1-C2**: 无破坏性变更和命名无冲突
5. **T1-T3**: 服务器启动后 MCP 功能正常

### 验证方法

```bash
# 文档完整性验证
ls docs/mcp-service-optimization/0*_*.md | wc -l  # 应为 6

# MCP 端点可达性
curl -s -o /dev/null -w "%{http_code}" https://api.effiy.cn/mcp

# operation_id 检查（代码层）
grep -rn "operation_id" src/api/routes/state.py src/api/routes/observer_health.py
```

## Postscript: Future Planning & Improvements

- 将动态检查清单中的可自动化项（S2, F1-F3, C2）集成到 CI 管道
- 增加 MCP 工具调用端到端测试用例

## Workflow Standardization Review
1. **Repetitive labor identification**: operation_id 存在性的检查可自动化（grep/CI），无需人工逐项核对
2. **Decision criteria missing**: 缺少"什么情况下一个检查项可从 P0 降级为 P1"的标准
3. **Information silos**: 检查项分散在 01-05 各文档的 Acceptance Criteria 中，无统一汇总
4. **Feedback loop**: 清单验证结果无结构化记录机制（哪些项经常失败、哪些过时）

## System Architecture Evolution Thinking
- **A1. Current architecture bottleneck**: 检查清单为静态文档，验证结果需人工记录和汇总
- **A2. Next natural evolution node**: CI 集成的自动化验证 + 检查结果结构化存储（如 JSON 报告）
- **A3. Risks and rollback plans for evolution**: 自动化可能漏检语义层面的问题（如工具描述虽存在但不准确），需保留人工抽查
