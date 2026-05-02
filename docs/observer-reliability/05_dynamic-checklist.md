# Observer Reliability — Dynamic Checklist

> **Document Version**: v1.0 | **Last Updated**: 2026-05-03 | **Upstream**: [02 Requirement Tasks](./02_requirement-tasks.md), [03 Design Document](./03_design-document.md)>

[General Checks](#general-checks) | [Scenario Verification](#scenario-verification) | [Feature Implementation](#feature-implementation) | [Code Quality](#code-quality) | [Testing](#testing) | [Check Summary](#check-summary)

---

## General Checks

| Check Item | Priority | Status | Notes |
|-----------|----------|--------|-------|
| Title format correct | P0 | ⏳ Pending | 标题使用 `# Feature Name — Document Type` |
| Linked document links valid | P0 | ⏳ Pending | 01→02→03→04 相互链接可点击 |
| Related files created/updated | P0 | ⏳ Pending | `src/core/observer/` 目录及文件已创建或计划创建 |
| Project buildable | P0 | ⏳ Pending | `python main.py` 可启动，无导入错误 |

---

## Scenario Verification

### S1: Request Throttled Under Load

**Linked Requirement Tasks**: [02#S1](./02_requirement-tasks.md#scenario-s1-request-throttled-under-load)
**Linked Design Document**: [03#S1](./03_design-document.md#scenario-s1-request-throttled-under-load)
**Verification Tool Recommendation**: `pytest` + `fastapi.testclient.TestClient` / `locust` 压测

#### Preconditions Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| Observer 已启用 | P0 | ⏳ Pending | `config.yaml` 中 `observer_enabled=true` |
| Throttle 组件已初始化 | P0 | ⏳ Pending | `/health/observer` 返回 `throttle_enabled=true` |
| 客户端 IP 不在白名单 | P0 | ⏳ Pending | 确认请求 IP 未在 `observer_throttle_whitelist` 中 |

#### Operation Steps Verification

| Step | Description | Priority | Status | Verification Method |
|------|-------------|----------|--------|---------------------|
| 1 | 发送请求到 `/execution` | P0 | ⏳ Pending | `TestClient.get("/execution")` 返回 200 |
| 2 | 快速发送超过阈值数量的请求 | P0 | ⏳ Pending | 循环发送 110 次，最后 10 次返回 429 |
| 3 | 检查 429 响应头 | P0 | ⏳ Pending | `response.headers["Retry-After"]` 存在且为正整数 |
| 4 | 等待窗口重置后再次请求 | P1 | ⏳ Pending | 等待 `window_seconds` 后请求恢复 200 |

#### Expected Results Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| 超限返回 429 | P0 | ⏳ Pending | HTTP status code 断言 |
| 未超限返回 200 | P0 | ⏳ Pending | HTTP status code 断言 |
| 内存不随请求量增长 | P0 | ⏳ Pending | 压测前后进程 RSS 对比 |

#### Verification Focus Points

| Focus Point | Priority | Status | Verification Method |
|------------|----------|--------|---------------------|
| 白名单客户端不受限 | P1 | ⏳ Pending | 白名单 IP 发送 200 次仍返回 200 |
| 429 响应格式符合项目规范 | P1 | ⏳ Pending | `{"code":1003,"message":"..."}` |
| 时间戳过期清理正常 | P1 | ⏳ Pending | 长时间运行后内存不泄漏 |

---

### S2: Tail Sampling Captures Slow Request

**Linked Requirement Tasks**: [02#S2](./02_requirement-tasks.md#scenario-s2-tail-sampling-captures-slow-request)
**Linked Design Document**: [03#S2](./03_design-document.md#scenario-s2-tail-sampling-captures-slow-request)
**Verification Tool Recommendation**: `pytest` + `unittest.mock` 模拟慢请求

#### Preconditions Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| Tail Sampler 已启用 | P0 | ⏳ Pending | `/health/observer` 返回 `sampler_enabled=true` |
| 采样缓冲区未满 | P0 | ⏳ Pending | `sampler_buffer_size < sampler_buffer_max` |

#### Operation Steps Verification

| Step | Description | Priority | Status | Verification Method |
|------|-------------|----------|--------|---------------------|
| 1 | 发送正常请求 | P0 | ⏳ Pending | 请求耗时 10ms，不进入采样 |
| 2 | 发送慢请求（模拟） | P0 | ⏳ Pending | Mock 延迟 5s，触发采样 |
| 3 | 发送错误请求 | P0 | ⏳ Pending | 请求返回 500，触发采样 |
| 4 | 检查采样 buffer | P0 | ⏳ Pending | `/health/observer` 包含慢请求和错误记录 |

#### Expected Results Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| 慢请求被采样 | P0 | ⏳ Pending | buffer 中存在 `duration_ms > 5000` 的记录 |
| 错误请求被采样 | P0 | ⏳ Pending | buffer 中存在 `status_code=500` 的记录 |
| Buffer 大小固定 | P0 | ⏳ Pending | 超过 maxlen 后旧记录被覆盖 |

#### Verification Focus Points

| Focus Point | Priority | Status | Verification Method |
|------------|----------|--------|---------------------|
| 正常请求不被过度采样 | P1 | ⏳ Pending | 大量 200 请求后 buffer 中仍有异常记录 |
| Buffer 满时循环覆盖 | P1 | ⏳ Pending | 发送 2000 次请求，buffer 大小始终 ≤ 1000 |
| 采样数据结构完整 | P1 | ⏳ Pending | 每条记录包含 request_id, path, duration_ms, status_code |

---

### S3: Sandbox Blocks File Access

**Linked Requirement Tasks**: [02#S3](./02_requirement-tasks.md#scenario-s3-sandbox-blocks-file-access)
**Linked Design Document**: [03#S3](./03_design-document.md#scenario-s3-sandbox-blocks-file-access)
**Verification Tool Recommendation**: `pytest` + 临时文件系统

#### Preconditions Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| Sandbox 已启用 | P0 | ⏳ Pending | `/health/observer` 返回 `sandbox_enabled=true` |
| 文件系统规则已加载 | P0 | ⏳ Pending | `config.yaml` 中 `observer_sandbox_fs_allowlist` 非空 |

#### Operation Steps Verification

| Step | Description | Priority | Status | Verification Method |
|------|-------------|----------|--------|---------------------|
| 1 | 模块读取 allowlist 内文件 | P0 | ⏳ Pending | 读取 `/tmp/allowed.txt` 成功 |
| 2 | 模块读取 allowlist 外文件 | P0 | ⏳ Pending | 读取 `/etc/passwd` 被阻止 |
| 3 | 模块通过符号链接跳转 | P1 | ⏳ Pending | `/tmp/link -> /etc/passwd` 被阻止 |
| 4 | 检查日志 | P1 | ⏳ Pending | 日志中包含 `SandboxViolation` 和堆栈 |

#### Expected Results Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| 允许路径正常通过 | P0 | ⏳ Pending | 读取成功，数据正确 |
| 非允许路径被阻止 | P0 | ⏳ Pending | 抛出 `SandboxViolation` |
| 符号链接被正确解析 | P1 | ⏳ Pending | 解析后路径不在 allowlist 中 |

#### Verification Focus Points

| Focus Point | Priority | Status | Verification Method |
|------------|----------|--------|---------------------|
| 沙箱仅影响 executor/MCP | P1 | ⏳ Pending | 普通 API 路由的 `open()` 不受影响 |
| 异常后原始 `open` 恢复 | P1 | ⏳ Pending | 沙箱上下文退出后正常 `open` 可用 |
| 日志为结构化 JSON | P1 | ⏳ Pending | 日志可被 `json.loads()` 解析 |

---

### S4: Lazy Start on First Request

**Linked Requirement Tasks**: [02#S4](./02_requirement-tasks.md#scenario-s4-lazy-start-on-first-request)
**Linked Design Document**: [03#S4](./03_design-document.md#scenario-s4-lazy-start-on-first-request)
**Verification Tool Recommendation**: `pytest` + `asyncio` / 启动时间测试

#### Preconditions Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| `observer_lazy_start=true` | P0 | ⏳ Pending | `config.yaml` 配置确认 |
| 应用刚启动 | P0 | ⏳ Pending | 无请求到达过 |

#### Operation Steps Verification

| Step | Description | Priority | Status | Verification Method |
|------|-------------|----------|--------|---------------------|
| 1 | 启动应用 | P0 | ⏳ Pending | `create_app()` 完成时间 < 50ms |
| 2 | 发送 Health check | P0 | ⏳ Pending | `/health` 返回 200，不触发懒加载 |
| 3 | 发送第一个业务请求 | P0 | ⏳ Pending | 首次请求耗时略高（含初始化） |
| 4 | 发送第二个业务请求 | P1 | ⏳ Pending | 后续请求耗时恢复正常 |

#### Expected Results Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| 启动时间增加 < 50ms | P0 | ⏳ Pending | `time.perf_counter()` 测量 |
| Health check 不触发初始化 | P0 | ⏳ Pending | 检查组件内部 `_initialized` 标志 |
| 并发首个请求无竞态 | P1 | ⏳ Pending | 10 个并发请求同时到达，仅初始化一次 |

#### Verification Focus Points

| Focus Point | Priority | Status | Verification Method |
|------------|----------|--------|---------------------|
| 关闭时清理懒加载资源 | P1 | ⏳ Pending | 应用关闭日志显示资源释放 |
| 初始化失败不影响后续请求 | P1 | ⏳ Pending | Mock 初始化失败，下次请求重试 |

---

### S5: Re-entrant Execution Detected

**Linked Requirement Tasks**: [02#S5](./02_requirement-tasks.md#scenario-s5-re-entrant-execution-detected)
**Linked Design Document**: [03#S5](./03_design-document.md#scenario-s5-re-entrant-execution-detected)
**Verification Tool Recommendation**: `pytest` + `asyncio` / Mock 回调

#### Preconditions Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| Reentrancy Guard 已启用 | P0 | ⏳ Pending | `/health/observer` 返回 `guard_enabled=true` |
| 默认深度限制为 3 | P0 | ⏳ Pending | `config.yaml` 或默认值确认 |

#### Operation Steps Verification

| Step | Description | Priority | Status | Verification Method |
|------|-------------|----------|--------|---------------------|
| 1 | 外层调用 execute_module | P0 | ⏳ Pending | 深度=1，正常执行 |
| 2 | 模块回调 /execution | P0 | ⏳ Pending | 深度=2，正常执行 |
| 3 | 第二层再次回调 | P0 | ⏳ Pending | 深度=3，正常执行 |
| 4 | 第三层再次回调 | P0 | ⏳ Pending | 深度将达到 4，返回 508 |

#### Expected Results Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| 前三层正常完成 | P0 | ⏳ Pending | 返回 200 和业务结果 |
| 第四层返回 508 | P0 | ⏳ Pending | HTTP status code 508 |
| 不同 Task 不共享深度 | P0 | ⏳ Pending | 并发请求各自独立计数 |

#### Verification Focus Points

| Focus Point | Priority | Status | Verification Method |
|------------|----------|--------|---------------------|
| 异常时深度正确回滚 | P1 | ⏳ Pending | 在第二层抛异常，depth 恢复到 0 |
| 508 响应包含当前深度 | P1 | ⏳ Pending | 响应 body 或头包含深度信息 |
| 守卫不阻止合法并发 | P1 | ⏳ Pending | 10 个不同客户端同时调用，均成功 |

---

## Feature Implementation Checks

### Core Features

| Check Item | Priority | Status | Linked Design Document Chapter |
|-----------|----------|--------|-------------------------------|
| `ThrottleMiddleware` 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `TailSampler` 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `SandboxMiddleware` 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `LazyStartManager` 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `ReentrancyGuard` 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `/health/observer` 路由 | P1 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `execute_module` 集成沙箱 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `execute_module` 集成守卫 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `main.py` 中间件注册 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `main.py` MCP 覆盖 | P1 | ⏳ Pending | [03 Implementation Details](#implementation-details) |

### Boundary and Error Handling

| Check Item | Priority | Status | Linked Design Document Chapter |
|-----------|----------|--------|-------------------------------|
| Observer 故障不穿透业务层 | P0 | ⏳ Pending | [03 Design Overview](#design-overview) |
| 429 响应格式符合规范 | P1 | ⏳ Pending | [03 Data Structure Design](#data-structure-design) |
| 403/508 响应格式符合规范 | P1 | ⏳ Pending | [03 Data Structure Design](#data-structure-design) |
| 配置缺失时使用安全默认值 | P1 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| 异常时 ContextVar 正确清理 | P1 | ⏳ Pending | [03 Implementation Details](#implementation-details) |

---

## Code Quality Checks

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| Style compliance (Ruff) | P1 | ⏳ Pending | `ruff check src/core/observer/` |
| Naming clarity | P1 | ⏳ Pending | 类名 CapWords，函数 snake_case |
| Type annotations coverage | P1 | ⏳ Pending | 所有公共函数参数和返回值有类型注解 |
| Performance (middleware overhead) | P2 | ⏳ Pending | 微基准测试单请求开销 < 1ms |
| Security risks | P0 | ⏳ Pending | SAST 扫描沙箱和限流逻辑 |

---

## Testing Checks

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| Unit coverage core (observer/) | P1 | ⏳ Pending | `pytest tests/core/observer/` |
| E2E coverage main scenarios (S1-S5) | P0 | ⏳ Pending | `pytest tests/e2e/test_observer.py` |
| P0 tests all passed | P0 | ⏳ Pending | `pytest -m "p0"` 全部通过 |
| Test report complete | P1 | ⏳ Pending | `pytest --cov=src/core/observer --cov-report=html` |

---

## Check Summary

### Overall Progress

| Category | Total | Completed | Pass Rate |
|----------|-------|-----------|-----------|
| General Checks | 4 | 0 | 0% |
| Scenario Verification | 42 | 0 | 0% |
| Feature Implementation | 15 | 0 | 0% |
| Code Quality | 5 | 0 | 0% |
| Testing | 4 | 0 | 0% |
| **Total** | **70** | **0** | **0%** |

### Pending Items

- [ ] General Checks: 全部 4 项待验证
- [ ] S1 Verification: 全部 10 项待验证
- [ ] S2 Verification: 全部 10 项待验证
- [ ] S3 Verification: 全部 10 项待验证
- [ ] S4 Verification: 全部 10 项待验证
- [ ] S5 Verification: 全部 10 项待验证
- [ ] Feature Implementation: 全部 15 项待编码验证
- [ ] Code Quality: 全部 5 项待检查
- [ ] Testing: 全部 4 项待执行

### Conclusion

⏳ 检查尚未开始。等待 `implement-code` 阶段完成后，根据实际代码和测试结果回填本清单。

---

## Postscript: Future Planning & Improvements

1. **自动化测试触发**：CI 中增加 observer 专项测试 stage，自动运行所有 P0 场景。
2. **性能基线门禁**：在 PR 中增加微基准测试，若中间件开销 > 1ms 则拒绝合并。
3. **混沌测试**：定期运行故障注入测试，验证 Observer 的故障隔离能力。
4. **覆盖率追踪**：将 `src/core/observer/` 的测试覆盖率目标设为 90%，低于则告警。
5. **文档同步**： checklist 更新后自动触发 `import-docs`，确保远程文档 API 同步。
