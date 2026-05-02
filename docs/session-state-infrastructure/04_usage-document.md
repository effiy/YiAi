# Session & State Infrastructure — Usage Document

> **Document Version**: v1.0 | **Last Updated**: 2026-05-03 | **Upstream**: [03 Design Document](./03_design-document.md)>

[Feature Intro](#feature-intro) | [Quick Start](#quick-start) | [Operation Scenarios](#operation-scenarios) | [FAQ](#faq) | [Tips](#tips)

---

## Feature Introduction

Session & State Infrastructure 为 YiAi 提供了一套统一的状态管理能力。通过结构化状态仓库，你可以安全地保存、查询和导出各类运行时数据；通过会话适配器，你能将现有遗留会话数据转换为类型安全的结构化记录；通过技能执行记录器，系统会自动收集技能运行表现，为后续优化提供数据支撑。配套的命令行工具让你无需启动 HTTP 服务即可完成大部分运维操作。

🎯 **统一存储**：一条 API 或一个 CLI 命令即可存取任何结构化状态。

⚡ **离线运维**：CLI 直接连接 MongoDB，服务停机也能查数据。

🔧 **即插即用**：技能记录器自动工作，无需修改业务代码。

**目标受众**：后端开发者、系统运维人员、AI 技能开发者。

---

## Quick Start

### Prerequisites

- [ ] Python 3.10+
- [ ] MongoDB 可访问（与 FastAPI 服务使用同一实例）
- [ ] `typer` 已安装（`pip install typer`）
- [ ] `config.yaml` 中已配置 `mongodb_url`

### 30-Second Onboarding

1. **创建状态记录**
   ```bash
   curl -X POST http://localhost:8000/state/records \
     -H "Content-Type: application/json" \
     -d '{"record_type":"test","title":"hello","payload":{"x":1}}'
   ```

2. **查询记录**
   ```bash
   curl "http://localhost:8000/state/records?record_type=test"
   ```

3. **使用 CLI 查询**
   ```bash
   python -m src.cli.state_query list --record-type test
   ```

4. **导出为 JSON**
   ```bash
   python -m src.cli.state_query list --record-type test --format json --output out.json
   ```

---

## Operation Scenarios

### Scenario 1: Saving Application State

**Applicable Situation**: 你的服务需要保存一个中间计算结果，供后续步骤或外部系统读取。

**Operation Steps**:
1. 构造 POST 请求到 `/state/records`。
2. 填写 `record_type`（如 `calculation_result`）、`title`、`payload` 和可选的 `tags`。
3. 保存返回的 `key`，用于后续查询或更新。

**Expected Results**: 服务端返回 `201 Created`，body 包含 `{"key": "..."}`。

**Notes**:
- ✅ `payload` 可以是任意 JSON 对象，没有固定模式。
- ❌ `record_type` 不能为空字符串。

### Scenario 2: Searching and Filtering States

**Applicable Situation**: 你需要在大量状态记录中找出特定类型的数据。

**Operation Steps**:
1. 发送 GET `/state/records?record_type=conversation_summary&title=onboarding`。
2. 如需时间范围，添加 `created_after` 和 `created_before`（ISO 8601 格式）。
3. 如需分页，添加 `page_num` 和 `page_size`。

**Expected Results**: 返回分页列表，包含匹配的记录。

**Notes**:
- ✅ 所有过滤条件可组合使用，关系为 AND。
- ✅ `title` 搜索大小写不敏感。
- ❌ `page_size` 最大 8000，超过会被截断。

### Scenario 3: Adapting a Legacy Session

**Applicable Situation**: 你需要将旧版 `sessions` 集合中的数据转换为新的结构化格式。

**Operation Steps**:
1. 在 Python 环境中导入 `SessionAdapter`：
   ```python
   from services.state.session_adapters import SessionAdapter
   ```
2. 传入单个 session 字典：`adapted = SessionAdapter.adapt(raw_doc)`。
3. 批量处理时使用 `SessionAdapter.adapt_batch(cursor, batch_size=100)`。

**Expected Results**: 得到 `SessionState` Pydantic 模型；批量处理返回 `AdaptationResult`。

**Notes**:
- ✅ 字段缺失时会使用默认值，不会抛异常。
- ❌ `pageContent` 和 `messages` 以外的自定义字段会放入 `metadata`。

### Scenario 4: Exporting Data for Analysis

**Applicable Situation**: 你需要将状态数据导出给数据分析团队或备份到文件。

**Operation Steps**:
1. 使用 CLI 查询并导出：
   ```bash
   python -m src.cli.state_query list \
     --record-type skill_execution \
     --since 7d \
     --format csv \
     --output weekly.csv
   ```
2. 打开 `weekly.csv` 进行查看或进一步处理。

**Expected Results**: 生成包含表头和数据行的 CSV 文件。

**Notes**:
- ✅ 支持 `table`（默认）、`json`、`csv` 三种格式。
- ✅ `--since` 支持 `Nd`（N 天）、`Nh`（N 小时）简写。
- ❌ 导出大量数据时建议使用 `--format json`，避免表格换行问题。

### Scenario 5: Checking Skill Execution Health

**Applicable Situation**: 你想快速了解最近技能执行的成功率和耗时分布。

**Operation Steps**:
1. 运行统计命令：
   ```bash
   python -m src.cli.state_query stats --record-type skill_execution --since 1d
   ```
2. 查看输出的计数和平均耗时。

**Expected Results**: 终端显示按状态分组的统计表格。

**Notes**:
- ✅ 统计命令不返回原始数据，仅返回聚合结果，性能开销小。
- ❌ 如果记录器未启用（`state_store_enabled=false`），统计结果为空。

---

## FAQ

### 💡 Basics

**Q1: State Store 和现有的 `sessions` 集合有什么区别？**

A: `sessions` 是遗留的无模式集合，专门用于会话数据。State Store 是新的通用结构化仓库，使用独立的 `state_records` 集合，支持任意类型的状态记录，并提供统一的查询接口。

**Q2: 我可以用 State Store 替换 `sessions` 吗？**

A: 目前不建议直接替换。推荐使用 Session Adapter 将 `sessions` 数据转换为 `SessionState`，再按需写入 `state_records`。未来可能会提供官方迁移工具。

**Q3: CLI 需要 FastAPI 服务在运行吗？**

A: 不需要。CLI 直接连接 MongoDB，适合运维和脚本场景。

### ⚙️ Advanced

**Q4: `payload` 有大小限制吗？**

A: 受 MongoDB 单文档 16MB 限制。建议将大文件引用（如 URL）放入 `payload`，而非原始内容。

**Q5: 如何为 State Store 添加自定义索引？**

A: 在 `StateStoreService.initialize()` 中通过 `create_index` 添加。日常查询若发现性能问题，可在该服务中扩展索引定义。

**Q6: Skill Recorder 记录失败会影响我的模块执行吗？**

A: 不会。记录器采用 fire-and-forget 异步模式，任何记录失败都不会抛回执行器。

### 🔧 Troubleshooting

**Q7: CLI 连接 MongoDB 失败怎么办？**

A: 检查 `config.yaml` 中的 `mongodb_url` 是否可访问；确认 MongoDB 服务已启动；检查网络防火墙。

**Q8: 查询结果为空，但我确定有数据。**

A: 检查过滤条件的大小写（`record_type` 是大小写敏感的）；检查时间格式是否为 ISO 8601；确认数据是否在 `state_records` 集合而非 `sessions`。

**Q9: Session Adapter 报错 `ValidationError`。**

A: 检查输入文档是否包含非预期类型（如 `messages` 不是列表）。可在调用 `adapt` 前打印文档结构进行排查。

**Q10: 如何清理过期的状态记录？**

A: 目前需要手动删除或通过 MongoDB TTL 索引自动清理。P2 规划中将提供内置的自动清理功能。

---

## Tips and Hints

### 💡 Practical Tips

1. **使用 Tags 组织数据**：为同类记录打上多个标签，查询时可通过 `tags` 参数快速过滤。
2. **标题搜索优化**：`title` 支持模糊搜索，适合快速定位记录，但不适合精确匹配。精确匹配建议使用 `payload` 中的特定字段。
3. **分页默认值**：API 默认返回 2000 条，适合大部分场景。大数据量导出时建议使用 CLI 的 `export` 子命令。

### ⌨️ Shortcuts

- CLI 支持 `--help` 查看所有子命令和参数说明。
- 使用 `--format json | jq '.list[].title'` 可快速提取特定字段。

### 📚 Best Practices

1. **保持 `record_type` 命名规范**：使用 snake_case，如 `conversation_summary`、`skill_execution`，避免空格和特殊字符。
2. **不要存储敏感信息**：`payload` 目前无加密，避免在状态记录中存放密码、Token 等敏感数据。
3. **监控记录器健康**：定期检查日志中 `SkillRecorder failed` 的报错，确保执行数据完整采集。

---

## Appendix

### Command Cheat Sheet

| Command | Description |
|---------|-------------|
| `python -m src.cli.state_query list --record-type X` | 列出某类型的记录 |
| `python -m src.cli.state_query get --key <key>` | 获取单条记录 |
| `python -m src.cli.state_query export --record-type X --output file.json` | 导出记录到文件 |
| `python -m src.cli.state_query stats --record-type X --since 1d` | 查看统计数据 |

### Related Resources

- [Design Document](./03_design-document.md)
- [Requirement Tasks](./02_requirement-tasks.md)
- [State Management](../state-management.md)

---

## Postscript: Future Planning & Improvements

1. **REPL 模式**：CLI 增加交互式 shell，支持逐条查询和即时修改。
2. **自动补全**：为 bash/zsh 生成 shell completion 脚本。
3. **可视化看板**：基于 `skill_execution` 数据提供 Web 看板，展示成功率和耗时趋势。
4. **多租户隔离**：在 `StateRecord` 中增加 `tenant_id` 字段，支持多租户场景。
5. **增量同步**：提供从 `sessions` 到 `state_records` 的增量同步命令，减少迁移开销。
