# Observer Reliability

> **Document Version**: v1.0 | **Last Updated**: 2026-05-03 | **Maintainer**: Claude | **Tool**: Claude Code
>
> **Related Documents**: [Requirement Tasks](./02_requirement-tasks.md) | [Design Document](./03_design-document.md) | [Usage Document](./04_usage-document.md) | [CLAUDE.md](../../CLAUDE.md)
>

[Feature Overview](#feature-overview) | [User Stories](#user-stories) | [Acceptance Criteria](#acceptance-criteria) | [Feature Details](#feature-details)

---

## Feature Overview

YiAi 当前缺乏对 MCP（Model Context Protocol）和动态模块执行的可观测性与可靠性控制。`fastapi-mcp` 已挂载但无访问隔离；`execution/executor.py` 支持动态调用任意白名单模块，却既无沙箱隔离也无执行前后的观测钩子；中间件层仅有认证，缺少请求节流和防重入保护。在高并发或异常输入场景下，系统面临内存膨胀、重复触发、过早初始化等稳定性风险。

本功能构建一套 Observer Reliability 基础设施，以中间件和装饰器形式为现有 MCP 端点、HTTP API 和模块执行引擎提供四层防护：内存与请求节流（带尾部采样）、沙箱访问控制、懒启动（lazy-start）资源管理、以及重入守卫。Observer 本身以非侵入方式接入现有请求链和生命周期，不修改业务逻辑，仅在外围提供限流、观测和安全加固。

🎯 **可控可观测**：为所有 MCP/API/Execution 入口增加统一的节流、采样和访问控制。

⚡ **资源保护**：通过懒启动和重入守卫避免重复初始化和递归放大，降低内存与 CPU 峰值。

🔧 **安全加固**：沙箱访问修复确保 MCP 和 Execution 在受限权限下运行，防止越权访问主机资源。

---

## User Stories

**Priority**: 🔴 P0 | 🟡 P1 | 🟢 P2

| User Story | Acceptance Criteria | Process-Generated Documents | Output Smart Documents |
|------------|---------------------|----------------------------|------------------------|
| 🔴 As a system operator, I want request throttling and tail sampling on MCP and API endpoints, so that memory explosion under high load is prevented.<br/><br/>**Main Operation Scenarios**:<br/>- Request rate exceeds threshold and gets throttled<br/>- Tail sampling records slow/errored requests for analysis<br/>- Throttle state is observable via a health endpoint | 1. Per-client rate limit configurable (req/sec)<br>2. Excess requests receive 429 with Retry-After<br>3. Tail sampler captures top 5% slowest and all errors<br>4. Memory footprint stays within configured budget under load test | [Requirement Tasks](./02_requirement-tasks.md)<br>[Design Document](./03_design-document.md)<br>[Project Report](./07_project-report.md) | [Generate Document Skill](../../.claude/skills/generate-document/SKILL.md)<br>[Requirement Document Specification](../../.claude/skills/generate-document/rules/requirement-document.md) |
| 🔴 As a security engineer, I want sandbox access control around module execution and MCP, so that untrusted code cannot access sensitive host resources.<br/><br/>**Main Operation Scenarios**:<br/>- A module tries to read /etc/passwd and is blocked<br/>- MCP tool access is restricted to allowlisted directories<br/>- Sandbox violations are logged with full context | 1. File-system sandbox blocks paths outside allowlist<br>2. Network sandbox blocks non-allowlisted outbound hosts<br>3. MCP tools run under sandbox by default<br>4. Violations emit structured logs with stack trace | [Requirement Tasks](./02_requirement-tasks.md)<br>[Design Document](./03_design-document.md)<br>[Project Report](./07_project-report.md) | [Generate Document Skill](../../.claude/skills/generate-document/SKILL.md)<br>[Requirement Document Specification](../../.claude/skills/generate-document/rules/requirement-document.md) |
| 🟡 As a backend developer, I want lazy-start initialization for heavy observer components, so that cold-start time and resource waste are reduced.<br/><br/>**Main Operation Scenarios**:<br/>- Observer services initialize only on first request<br/>- Health check does not trigger heavy component startup<br/>- Shutdown gracefully cleans up lazily started resources | 1. Throttle store, sampler, and sandbox initialize on first use<br>2. `create_app()` lifespan does not block on observer setup<br>3. Thread-safe lazy init with double-checked locking<br>4. Startup time increase < 50ms | [Requirement Tasks](./02_requirement-tasks.md)<br>[Design Document](./03_design-document.md)<br>[Project Report](./07_project-report.md) | [Generate Document Skill](../../.claude/skills/generate-document/SKILL.md)<br>[Requirement Document Specification](../../.claude/skills/generate-document/rules/requirement-document.md) |
| 🟡 As the system, I want re-entrancy guards on observer middleware and execution hooks, so that recursive or cyclic invocations do not stack-overflow or deadlock.<br/><br/>**Main Operation Scenarios**:<br/>- An execution module calls back into /execution and is detected<br/>- Observer middleware avoids self-triggering on internal subrequests<br/>- Cyclic call chains are detected and broken | 1. Reentrancy depth limit configurable (default 3)<br>2. Exceeded depth returns 508 Loop Detected<br>3. Guards are per-async-context (asyncio Task local)<br>4. No false positives on legitimate concurrent requests | [Requirement Tasks](./02_requirement-tasks.md)<br>[Design Document](./03_design-document.md)<br>[Project Report](./07_project-report.md) | [Generate Document Skill](../../.claude/skills/generate-document/SKILL.md)<br>[Requirement Document Specification](../../.claude/skills/generate-document/rules/requirement-document.md) |

---

## Document Specifications

1. **01_requirement-document.md** (this document): What the feature does, scope, and acceptance criteria.
2. **02_requirement-tasks.md**: Scenarios, impact analysis, verifiable tasks.
3. **03_design-document.md**: Architecture, module division, interface specs, data structures.
4. **04_usage-document.md**: End-user guide for operators and developers.
5. **05_dynamic-checklist.md**: Verifiable checklist for implementation and testing.
6. **07_project-report.md**: Delivery evidence and change summary.

---

## Acceptance Criteria

### P0 (Core)

- [ ] Throttle middleware limits requests per client/IP; excess returns 429.
- [ ] Tail sampler captures slow requests (> p95 latency) and all errors without memory growth.
- [ ] Sandbox middleware blocks file-system access outside allowlisted paths.
- [ ] Sandbox blocks outbound network calls to non-allowlisted hosts.
- [ ] Lazy-start initializes observer components on first real request, not during `create_app()`.
- [ ] Re-entrancy guard tracks call depth per async context and rejects when exceeding limit.
- [ ] All observer failures are logged but do not break the underlying request/execution.

### P1 (Important)

- [ ] Throttle and sampling configurations are hot-reloadable via `config.yaml`.
- [ ] Sandbox violations emit structured JSON logs with request ID and stack trace.
- [ ] Health endpoint `/health/observer` exposes throttle queue depth, sample buffer size, and sandbox block count.
- [ ] Re-entrancy guard supports configurable depth per route or module.
- [ ] Observer components can be selectively disabled via feature flags in `config.yaml`.

### P2 (Nice-to-have)

- [ ] Distributed rate limiting using Redis as shared counter backend.
- [ ] Adaptive throttling that adjusts limits based on memory pressure.
- [ ] WebSocket-aware sandbox for real-time MCP streaming.

---

## Feature Details

### 1. Memory Explosion Fix — Throttling and Tail Sampling

**Description**: Request throttling enforces per-client and global rate limits at the middleware layer, preventing unbounded request accumulation. Tail sampling records a bounded set of outlier requests (slowest and errors) for post-hoc analysis without retaining every request.

**Boundaries and Exceptions**:
- Throttle applies to HTTP API and MCP endpoints; static files and whitelisted paths are exempt.
- Tail sampler is in-memory only; does not replace persistent logging or APM.
- Sampling does not modify request/response bodies.

**Value/Motivation**: Prevents memory exhaustion from request buffering and log retention; provides actionable traces for the requests that matter most.

### 2. Sandbox Access Fix

**Description**: A sandbox middleware/interceptor that wraps module execution and MCP tool calls, restricting file-system and network access to explicitly allowlisted targets.

**Boundaries and Exceptions**:
- Sandbox does not wrap internal service-to-service calls (e.g., RSS scheduler to MongoDB).
- File-system sandbox uses path prefix matching; symbolic links are resolved before checking.
- Network sandbox operates at the `aiohttp`/`httpx` layer via custom transport or monkey-patch.

**Value/Motivation**: Mitigates supply-chain and prompt-injection risks where dynamically loaded modules or MCP tools might exfiltrate data or access sensitive files.

### 3. Lazy-Start Logic

**Description**: Heavy observer components (throttle token buckets, sampler ring buffers, sandbox rule caches) are initialized on first request rather than during application startup lifespan.

**Boundaries and Exceptions**:
- Lazy-start does not apply to database connections or RSS scheduler, which remain eager.
- Thread/async safety must be guaranteed during concurrent first-request races.
- Shutdown must still clean up lazily initialized resources.

**Value/Motivation**: Reduces cold-start time and avoids wasting resources on components that may never be used in a given deployment profile.

### 4. Re-entrancy Guard

**Description**: A context-local counter that increments on entry to guarded routes (Execution, MCP) and decrements on exit. If depth exceeds a threshold, the request is rejected with 508.

**Boundaries and Exceptions**:
- Guard is per-async-context (`contextvars` or `asyncio.Task` local), not global.
- Internal health checks and static file requests are not guarded.
- Legitimate concurrent requests from different clients must not trigger false positives.

**Value/Motivation**: Prevents accidental infinite recursion when modules call back into the API or when MCP tools trigger cascading invocations.

---

## Usage Scenario Examples

### Scenario 1: Throttling Under Load

📋 **Background**: A load test sends 1000 req/sec to `/execution`.

🎨 **Operation**:
1. Throttle middleware counts requests per IP.
2. At 100 req/sec (configurable), excess requests receive 429.
3. Tail sampler records the slowest 5% and all 500 errors.

📋 **Result**: System memory stays flat; sampled traces are available for analysis.

### Scenario 2: Blocking a Sandbox Violation

📋 **Background**: A dynamically loaded module attempts to read `/etc/passwd`.

🎨 **Operation**:
1. Sandbox interceptor wraps the module's `open()` call.
2. Path is not in allowlist; access is blocked.
3. Structured log emitted with request ID and traceback.

📋 **Result**: Module receives `PermissionError`; system logs the violation.

### Scenario 3: Detecting Re-entrant Execution

📋 **Background**: A module calls back into `/execution` during its own execution.

🎨 **Operation**:
1. Re-entrancy guard increments depth to 2.
2. Nested module calls `/execution` again; depth reaches 3 (limit).
3. Third nested call is rejected with 508.

📋 **Result**: Call chain is broken before stack overflow.

---

## Postscript: Future Planning & Improvements

1. **Distributed Throttling**: Replace in-memory token buckets with Redis-backed counters for multi-instance deployments.
2. **APM Integration**: Export tail-sampled spans to OpenTelemetry or Jaeger.
3. **Policy Engine**: Replace static allowlists with dynamic policy rules (e.g., time-based, role-based sandbox permissions).
4. **Lazy-Start Metrics**: Expose time-to-first-request and lazy-init overhead in Prometheus format.
5. **Re-entrancy Graph**: Build a call-graph of re-entrant chains to help developers refactor recursive logic.
