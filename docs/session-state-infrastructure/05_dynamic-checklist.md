# Session & State Infrastructure — Dynamic Checklist

> **Document Version**: v1.0 | **Last Updated**: 2026-05-03 | **Upstream**: [02 Requirement Tasks](./02_requirement-tasks.md), [03 Design Document](./03_design-document.md)>

[General Checks](#general-checks) | [Scenario Verification](#scenario-verification) | [Feature Implementation](#feature-implementation) | [Code Quality](#code-quality) | [Testing](#testing) | [Check Summary](#check-summary)

---

## General Checks

| Check Item | Priority | Status | Notes |
|-----------|----------|--------|-------|
| Title format correct | P0 | ⏳ Pending | 所有文档标题使用 `# Feature Name — Document Type` 格式 |
| Linked document links valid | P0 | ⏳ Pending | 01→02→03→04 相互链接可点击 |
| Related files created/updated | P0 | ⏳ Pending | `src/services/state/`, `src/cli/`, `src/api/routes/state.py` 已创建或计划创建 |
| Project buildable | P0 | ⏳ Pending | `pip install -r requirements.txt` 成功，`python main.py` 可启动 |

---

## Scenario Verification

### S1: Create and Query a State Record via HTTP API

**Linked Requirement Tasks**: [02#S1](./02_requirement-tasks.md#scenario-s1-create-and-query-a-state-record-via-http-api)
**Linked Design Document**: [03#S1](./03_design-document.md#scenario-s1-create-and-query-a-state-record-via-http-api)
**Verification Tool Recommendation**: `pytest` + `httpx.AsyncClient` / `fastapi.testclient.TestClient`

#### Preconditions Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| FastAPI 服务可启动 | P0 | ⏳ Pending | `python main.py` 无报错启动 |
| MongoDB 可连接 | P0 | ⏳ Pending | `db.initialize()` 成功 |
| `state_records` 集合可访问 | P0 | ⏳ Pending | `db.db[STATE_RECORDS].find_one()` 不抛异常 |

#### Operation Steps Verification

| Step | Description | Priority | Status | Verification Method |
|------|-------------|----------|--------|---------------------|
| 1 | POST `/state/records` 传入合法 Body | P0 | ⏳ Pending | `TestClient.post("/state/records", json={...})` 返回 201 |
| 2 | 返回体包含 `key` | P0 | ⏳ Pending | 断言 `"key" in response.json()` |
| 3 | GET `/state/records?record_type=X` 返回分页数据 | P0 | ⏳ Pending | 断言 `response.json()["list"]` 非空 |
| 4 | 分页参数越界时自动修正 | P1 | ⏳ Pending | `page_size=99999` 时返回数量 ≤ 8000 |

#### Expected Results Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| 创建成功返回 201 | P0 | ⏳ Pending | HTTP status code 断言 |
| 查询结果包含目标记录 | P0 | ⏳ Pending | 结果列表中存在匹配的 `key` |
| 非法参数返回 422 | P0 | ⏳ Pending | `record_type=""` 时返回 422 |

#### Verification Focus Points

| Focus Point | Priority | Status | Verification Method |
|------------|----------|--------|---------------------|
| Schema 校验拒绝非法字段 | P0 | ⏳ Pending | 传入未知顶级字段，验证是否被忽略或拒绝 |
| 查询支持大小写不敏感文本搜索 | P1 | ⏳ Pending | `title_contains=Hello` 能匹配 `hello world` |
| 分页元数据正确 | P1 | ⏳ Pending | 返回包含 `total`, `pageNum`, `pageSize`, `totalPages` |

---

### S2: Query and Export Records via CLI

**Linked Requirement Tasks**: [02#S2](./02_requirement-tasks.md#scenario-s2-query-and-export-records-via-cli)
**Linked Design Document**: [03#S2](./03_design-document.md#scenario-s2-query-and-export-records-via-cli)
**Verification Tool Recommendation**: `pytest` + `typer.testing.CliRunner`

#### Preconditions Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| `typer` 已安装 | P0 | ⏳ Pending | `import typer` 成功 |
| CLI 模块可导入 | P0 | ⏳ Pending | `from cli.state_query import app` 成功 |
| MongoDB 连接字符串有效 | P0 | ⏳ Pending | CLI 不依赖 HTTP 服务即可连接 |

#### Operation Steps Verification

| Step | Description | Priority | Status | Verification Method |
|------|-------------|----------|--------|---------------------|
| 1 | 运行 `list --record-type X` | P0 | ⏳ Pending | `CliRunner.invoke(app, ["list", "--record-type", "X"])` exit_code=0 |
| 2 | 终端输出表格 | P0 | ⏳ Pending | `result.output` 包含分隔线或标题 |
| 3 | `--format json --output file.json` 写入文件 | P0 | ⏳ Pending | 文件存在且包含 `"list"` 和 `"total"` |
| 4 | `--format csv --output file.csv` 写入文件 | P1 | ⏳ Pending | 文件存在且首行为表头 |

#### Expected Results Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| CLI 在 FastAPI 未启动时运行 | P0 | ⏳ Pending | 确认无 Uvicorn 进程时 CLI 仍可执行 |
| JSON 输出包含 `list` 和 `total` | P0 | ⏳ Pending | `json.loads(output)["total"] >= 0` |
| CSV 输出包含表头 | P1 | ⏳ Pending | 首行包含 `key,record_type,title,...` |

#### Verification Focus Points

| Focus Point | Priority | Status | Verification Method |
|------------|----------|--------|---------------------|
| CLI filter 逻辑与 API 一致 | P0 | ⏳ Pending | 同一组参数下 CLI 和 API 返回相同 `total` |
| `--since` 参数解析正确 | P1 | ⏳ Pending | `--since 1d` 仅返回最近 24 小时数据 |
| 空结果优雅处理 | P1 | ⏳ Pending | 无匹配记录时输出提示而非报错 |

---

### S3: Batch Adapt Legacy Sessions

**Linked Requirement Tasks**: [02#S3](./02_requirement-tasks.md#scenario-s3-batch-adapt-legacy-sessions)
**Linked Design Document**: [03#S3](./03_design-document.md#scenario-s3-batch-adapt-legacy-sessions)
**Verification Tool Recommendation**: `pytest` + `mongomock` / 真实 MongoDB 测试实例

#### Preconditions Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| `sessions` 集合存在测试数据 | P0 | ⏳ Pending | 插入包含 `pageContent` 和 `messages` 的文档 |
| `SessionAdapter` 已导入 | P0 | ⏳ Pending | `from services.state.session_adapters import SessionAdapter` |

#### Operation Steps Verification

| Step | Description | Priority | Status | Verification Method |
|------|-------------|----------|--------|---------------------|
| 1 | 调用 `adapt(raw_doc)` | P0 | ⏳ Pending | 返回 `SessionState` 实例 |
| 2 | 调用 `adapt_batch(cursor, 100)` | P0 | ⏳ Pending | 返回 `AdaptationResult` |
| 3 | 处理包含缺失字段的文档 | P1 | ⏳ Pending | 不抛异常，使用默认值 |
| 4 | 处理包含非法类型的文档 | P1 | ⏳ Pending | 记录到 `errors` 列表 |

#### Expected Results Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| `pageContent` 映射为 `page_content` | P0 | ⏳ Pending | `adapted.page_content == raw_doc["pageContent"]` |
| `messages` 映射为列表 | P0 | ⏳ Pending | `isinstance(adapted.messages, list)` |
| `AdaptationResult` 包含成功/失败计数 | P0 | ⏳ Pending | `result.success_count + result.failure_count == total` |

#### Verification Focus Points

| Focus Point | Priority | Status | Verification Method |
|------------|----------|--------|---------------------|
| 缺失 `messages` 时默认 `[]` | P1 | ⏳ Pending | 输入不含 `messages`，输出 `messages == []` |
| 空数组 `messages` 不触发错误 | P1 | ⏳ Pending | 输入 `messages=[]`，输出不记录为失败 |
| 批量 1000 条性能可接受 | P2 | ⏳ Pending | 耗时 < 5 秒 |

---

### S4: Record Skill Execution Outcome

**Linked Requirement Tasks**: [02#S4](./02_requirement-tasks.md#scenario-s4-record-skill-execution-outcome)
**Linked Design Document**: [03#S4](./03_design-document.md#scenario-s4-record-skill-execution-outcome)
**Verification Tool Recommendation**: `pytest` + `unittest.mock` / `pytest-asyncio`

#### Preconditions Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| `SkillRecorder` 已初始化 | P0 | ⏳ Pending | 实例化时不抛异常 |
| `execute_module` 可正常调用 | P0 | ⏳ Pending | 调用白名单模块返回预期结果 |

#### Operation Steps Verification

| Step | Description | Priority | Status | Verification Method |
|------|-------------|----------|--------|---------------------|
| 1 | 成功执行模块 | P0 | ⏳ Pending | `execute_module(...)` 返回成功结果 |
| 2 | 验证 `SkillRecorder` 被触发 | P0 | ⏳ Pending | Mock `record_async` 断言被调用一次 |
| 3 | 失败执行模块 | P0 | ⏳ Pending | `execute_module(...)` 抛出异常 |
| 4 | 验证失败记录包含 error_message | P0 | ⏳ Pending | Mock 断言 `error_message` 非空 |

#### Expected Results Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| 成功状态被记录 | P0 | ⏳ Pending | 数据库中存在 `status=success` 的记录 |
| 失败状态被记录 | P0 | ⏳ Pending | 数据库中存在 `status=failed` 的记录 |
| `duration_ms` 为正数 | P0 | ⏳ Pending | `record.duration_ms > 0` |
| 记录失败不影响执行结果 | P0 | ⏳ Pending | 即使 `record_async` 内部抛异常，执行结果不变 |

#### Verification Focus Points

| Focus Point | Priority | Status | Verification Method |
|------------|----------|--------|---------------------|
| 异步调用不阻塞返回 | P0 | ⏳ Pending | 执行总耗时无明显增加 |
| 记录失败仅打日志 | P1 | ⏳ Pending | `caplog` 捕获 `ERROR` 级别日志 |
| `skill_name` 与模块路径一致 | P1 | ⏳ Pending | `record.skill_name == module_path` |

---

## Feature Implementation Checks

### Core Features

| Check Item | Priority | Status | Linked Design Document Chapter |
|-----------|----------|--------|-------------------------------|
| `StateStoreService.create()` 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `StateStoreService.query()` 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `StateStoreService.get()` 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `StateStoreService.update()` 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `StateStoreService.delete()` 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `SessionAdapter.adapt()` 实现 | P1 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `SessionAdapter.adapt_batch()` 实现 | P1 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `SkillRecorder.record_async()` 实现 | P1 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| CLI `list` 子命令 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| CLI `get` 子命令 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| CLI `export` 子命令 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| CLI `stats` 子命令 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |

### Boundary and Error Handling

| Check Item | Priority | Status | Linked Design Document Chapter |
|-----------|----------|--------|-------------------------------|
| Schema 校验拒绝空 `record_type` | P0 | ⏳ Pending | [03 Data Structure Design](#data-structure-design) |
| 查询 `page_size` 越界自动截断 | P1 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| 适配器对缺失字段使用默认值 | P1 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| 记录器异常不传播到执行器 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| CLI 连接失败给出明确错误信息 | P1 | ⏳ Pending | [03 Usage Scenarios](#operation-scenarios) |

---

## Code Quality Checks

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| Style compliance (Ruff) | P1 | ⏳ Pending | `ruff check src/services/state/ src/cli/ src/api/routes/state.py` |
| Naming clarity | P1 | ⏳ Pending | 类名 CapWords，函数/变量 snake_case，常量 UPPER_SNAKE_CASE |
| Type annotations coverage | P1 | ⏳ Pending | 所有公共函数参数和返回值有类型注解 |
| Performance (query with index) | P2 | ⏳ Pending | `explain("executionStats")` 确认使用索引 |
| Security risks | P0 | ⏳ Pending | `payload` 不存放敏感信息；CLI 写操作需 `--write` 标志 |

---

## Testing Checks

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| Unit coverage core (StateStoreService) | P1 | ⏳ Pending | `pytest tests/services/state/test_state_service.py` |
| E2E coverage main scenarios (S1-S4) | P0 | ⏳ Pending | `pytest tests/e2e/test_state_api.py` |
| P0 tests all passed | P0 | ⏳ Pending | `pytest -m "p0"` 全部通过 |
| Test report complete | P1 | ⏳ Pending | `pytest --cov=src/services/state --cov-report=html` |

---

## Check Summary

### Overall Progress

| Category | Total | Completed | Pass Rate |
|----------|-------|-----------|-----------|
| General Checks | 4 | 0 | 0% |
| Scenario Verification | 32 | 0 | 0% |
| Feature Implementation | 16 | 0 | 0% |
| Code Quality | 5 | 0 | 0% |
| Testing | 4 | 0 | 0% |
| **Total** | **61** | **0** | **0%** |

### Pending Items

- [ ] General Checks: 全部 4 项待验证
- [ ] S1 Verification: 全部 12 项待验证
- [ ] S2 Verification: 全部 10 项待验证
- [ ] S3 Verification: 全部 10 项待验证
- [ ] S4 Verification: 全部 10 项待验证
- [ ] Feature Implementation: 全部 16 项待编码验证
- [ ] Code Quality: 全部 5 项待检查
- [ ] Testing: 全部 4 项待执行

### Conclusion

⏳ 检查尚未开始。等待 `implement-code` 阶段完成后，根据实际代码和测试结果回填本清单。

---

## Postscript: Future Planning & Improvements

1. **自动化回填**：在 CI 中集成 checklist 扫描脚本，自动根据 pytest 结果更新 Status 列。
2. **P0 门禁**：在合并请求中强制要求所有 P0 检查项为 ✅，否则禁止合并。
3. **性能基线**：为 `query()` 和 `adapt_batch()` 建立性能基线测试，回归时自动告警。
4. **安全审计**：增加 SAST 扫描，确保 `payload` 和 CLI 参数无注入风险。
5. **文档同步**： checklist 更新后自动触发 `import-docs`，确保远程文档 API 同步。
