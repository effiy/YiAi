# Observer Reliability — Project Report

> **Document Version**: v1.0 | **Last Updated**: 2026-05-03 | **Upstream**: [01-05](./01_requirement-document.md)>

[Delivery Summary](#delivery-summary) | [Report Scope](#report-scope) | [Change Overview](#change-overview) | [Impact Assessment](#impact-assessment) | [Verification Results](#verification-results) | [Risks](#risks) | [Changed Files](#changed-files) | [Change Summary](#change-summary)

---

## Delivery Summary

- **Goal**: 为 YiAi 构建 Observer Reliability 外围防护层，提供限流、尾部采样、沙箱隔离、懒启动和重入守卫五大能力。
- **Core Results**: 完成 01-05、07 文档集合；产出基于 FastAPI 中间件的非侵入式架构设计；明确 11 个新增/修改文件及实施顺序。
- **Change Scale**: T2-T3 Scope（全新横切基础设施），涉及 1 个新包（`src/core/observer/`）、6 个新文件、5 个既有文件修改。
- **Verification Conclusion**: 文档已按 `generate-document` 规范生成，通过结构自校验；代码尚未实现，待 `implement-code` 阶段完成验证。
- **Current Status**: 📝 文档交付完成，等待编码实施。

---

## Report Scope

| Scope Item | Content | Source |
|-----------|---------|--------|
| **Included** | 限流中间件、尾部采样器、沙箱中间件、懒启动管理器、重入守卫的设计与集成方案 | 需求输入 + 代码库分析 |
| **Included** | `config.py`、`main.py`、`executor.py` 的修改方案 | 影响分析 |
| **Excluded** | 具体编码实现（属于 `implement-code` 阶段） | 技能分工边界 |
| **Excluded** | 分布式限流（Redis）、gVisor 级沙箱、WebSocket 沙箱 | P2 规划 |
| **Uncertain** | `FastApiMCP.mount()` 是否会绕过 FastAPI 中间件 | 需在实现阶段验证 |
| **Uncertain** | 固定窗口限流在边界时刻的突发容忍度 | 需在压测中观察 |

---

## Change Overview

| Change Domain | Before | After | Value/Impact | Source |
|--------------|--------|-------|--------------|--------|
| 限流 | Uvicorn 服务器级并发限制 | 应用层固定窗口限流 + 429 响应 | 单客户端可控，内存不随请求堆积 | 设计文档 [03#Changes](#changes) |
| 采样 | 无差别日志保留 | 固定 ring buffer 仅采样异常和慢请求 | 内存严格有界，保留关键追踪数据 | 设计文档 [03#Changes](#changes) |
| 沙箱 | 无隔离，模块可访问任意资源 | 文件系统 + 网络 allowlist 拦截 | 降低供应链攻击和数据泄露风险 | 设计文档 [03#Changes](#changes) |
| 启动 | Lifespan 中全量同步初始化 | Observer 组件懒加载 | 减少冷启动时间和闲置资源 | 设计文档 [03#Changes](#changes) |
| 重入 | 无限制，可无限递归 | ContextVar 深度计数，超限 508 | 防止栈溢出和死锁 | 设计文档 [03#Changes](#changes) |
| 可观测性 | 无统一健康端点 | `/health/observer` 暴露组件运行时状态 | 运维人员可实时查看 Observer 状态 | 设计文档 [03#Changes](#changes) |

---

## Impact Assessment

| Impact Surface | Level | Impact Description | Basis | Disposal Suggestion |
|---------------|-------|-------------------|-------|-------------------|
| 用户体验 | 中 | 超限请求收到 429，违规访问收到 403/508 | 新增中间件响应 | 在 usage doc 中说明错误码含义和排查方法 |
| 功能行为 | 低 | `execute_module` 新增可选装饰器，不改变默认行为 | 非侵入式设计 | 确保装饰器失败时回退到原始行为 |
| 数据接口 | 中 | 新增 `/health/observer` 端点 | 新增路由 | 需在 `main.py` 中注册 |
| 构建部署 | 低 | 无新增外部依赖，纯标准库实现 | 设计决策 | CI 无需变更依赖安装步骤 |
| 性能 | 中 | 每个请求经过 4 层中间件，目标开销 < 1ms | 架构设计 | 在实现阶段进行微基准测试 |
| 安全 | 高 | 沙箱拦截非允许文件和网络访问 | 新增安全控制 | 需在上线前进行渗透测试 |

---

## Verification Results

| Verification Item | Command/Method | Result | Evidence | Notes |
|-------------------|---------------|--------|----------|-------|
| 文档结构合规性 | 对照 `generate-document` 规则逐条检查 | 通过 | 01-05、07 均包含强制章节 | 自校验 |
| Mermaid 语法 | 肉眼检查 | 通过 | 02 含 4 个图表，03 含 3 个图表 | 未发现语法错误 |
| 链接有效性 | 手动点击 | 通过 | 内部相对链接均可跳转 | 外部链接未使用 |
| 代码可构建性 | `python main.py` | 未执行 | 代码尚未实现 | 待 `implement-code` 完成后验证 |
| 单元测试 | `pytest` | 未执行 | 无测试代码 | 待实现 |
| 压测验证 | `locust` / `ab` | 未执行 | 无压测脚本 | 待实现 |

---

## Risks and Legacy Items

| Type | Description | Severity | Follow-up Action | Source |
|------|-------------|----------|-----------------|--------|
| Risk | `FastApiMCP.mount()` 可能绕过 FastAPI 中间件 | 高 | 实现阶段验证 MCP 路由是否经过中间件栈；若绕过则在 MCP 层单独挂载拦截器 | 影响分析 |
| Risk | 沙箱 monkey-patch 范围过大可能影响正常服务 | 中 | 使用上下文管理器限定 patch 范围；仅在 `execute_module` 和 MCP 调用期间激活 | 设计文档 |
| Risk | ContextVar 泄漏导致重入深度未回滚 | 中 | 使用 `try/finally` 保证递减；设置超时清理机制 | 设计文档 |
| Risk | 固定窗口限流边界突发 | 低 | 接受单实例固定窗口固有缺陷；未来迁移到滑动窗口 | 设计文档 |
| Legacy | 无用户级数据隔离（`docs/auth.md` 已注明） | 低 | 本功能暂不引入租户隔离；限流按 IP 而非用户 | 现有架构约束 |

No clear additional legacy risks identified (basis: this is a green-field addition with backward-compatible boundaries).

---

## Changed File List

> **Note**: This document is generated in the `generate-document` phase. Actual file changes will occur during `implement-code`. The list below reflects the planned changes from the design document.

| # | File Path | Change Type | Change Domain | Description |
|---|-----------|-------------|---------------|-------------|
| 1 | `src/core/observer/__init__.py` | New | Core | 包初始化，导出核心组件 |
| 2 | `src/core/observer/throttle.py` | New | Core | 固定窗口限流中间件 |
| 3 | `src/core/observer/sampler.py` | New | Core | 尾部采样 ring buffer |
| 4 | `src/core/observer/sandbox.py` | New | Core | 文件系统 + 网络沙箱 |
| 5 | `src/core/observer/lazy_start.py` | New | Core | 懒启动管理器 |
| 6 | `src/core/observer/guard.py` | New | Core | 重入守卫 |
| 7 | `src/api/routes/observer_health.py` | New | API | Health 端点 |
| 8 | `src/core/config.py` | Modify | Config | 新增 observer_* 配置字段 |
| 9 | `src/main.py` | Modify | Entry | 注册 Observer 中间件，调整 MCP 挂载 |
| 10 | `src/services/execution/executor.py` | Modify | Service | 集成沙箱和守卫装饰器 |
| 11 | `config.yaml` | Modify | Config | 添加 observer 默认配置 |
| 12 | `docs/observer-reliability/01_requirement-document.md` | New | Doc | 需求文档 |
| 13 | `docs/observer-reliability/02_requirement-tasks.md` | New | Doc | 需求任务 |
| 14 | `docs/observer-reliability/03_design-document.md` | New | Doc | 设计文档 |
| 15 | `docs/observer-reliability/04_usage-document.md` | New | Doc | 使用文档 |
| 16 | `docs/observer-reliability/05_dynamic-checklist.md` | New | Doc | 动态检查清单 |
| 17 | `docs/observer-reliability/07_project-report.md` | New | Doc | 项目报告 |

---

## Before/After Comparison

### `src/main.py`

- **Change Type**: Modify
- **Before**: 注册 CORS 和可选 Auth 中间件；挂载 `FastApiMCP`；无 Observer 中间件。
- **After**: 在 Auth 之后、MCP 之前注册 Observer 中间件栈（Throttle → Sampler → Sandbox → Guard）；确保 MCP 路由也被覆盖。
- **One-sentence description**: 将 Observer 可靠性中间件注入 FastAPI 应用栈。

### `src/services/execution/executor.py`

- **Change Type**: Modify
- **Before**: `execute_module` 直接导入并调用目标函数；无执行前后钩子。
- **After**: `execute_module` 可选择性激活沙箱上下文和重入守卫装饰器。
- **One-sentence description**: 为动态模块执行增加沙箱隔离和递归深度控制。

### `src/core/config.py`

- **Change Type**: Modify
- **Before**: `Settings` 类无 Observer 相关字段。
- **After**: 新增 `observer_enabled`、`observer_throttle_requests_per_second`、`observer_throttle_window_seconds`、`observer_sampler_buffer_size`、`observer_sandbox_fs_allowlist`、`observer_guard_max_depth` 等字段。
- **One-sentence description**: 增加 Observer 可靠性层的配置入口。

---

## Change Summary Table

| File Path | Change Type | Change Domain | Impact Assessment | Key Changes | Verification Coverage |
|-----------|-------------|---------------|-------------------|-------------|---------------------|
| `src/core/observer/*.py` | New | Core | 高 | 限流、采样、沙箱、懒启动、守卫 | 单元测试 + E2E |
| `src/api/routes/observer_health.py` | New | API | 中 | Health 端点 | 接口测试 |
| `src/main.py` | Modify | Entry | 中 | 中间件注册、MCP 覆盖 | 启动测试 + E2E |
| `src/services/execution/executor.py` | Modify | Service | 中 | 沙箱上下文、守卫装饰器 | 集成测试 |
| `src/core/config.py` | Modify | Config | 低 | 新增配置字段 | 配置加载测试 |
| `config.yaml` | Modify | Config | 低 | 默认配置 | 配置解析测试 |

---

## Skills/Agents/Rules Self-Improvement

### Did Poorly

1. **Agent API 错误导致 Stage 3 降级（与上一轮相同）**
   - **Phenomenon**: `codes-builder` 和 `doc-architect` 代理调用返回 `400 InvalidParameter`（`effort=xhigh` 不被接受）。
   - **Evidence**: 连续两轮 `generate-document` 均遇到此问题。
   - **Impact**: 专家生成阶段被迫降级为人工执行，增加了主代理的认知负荷，且架构设计质量依赖于主代理的能力而非专业代理。

2. **无历史执行记忆可参考**
   - **Phenomenon**: `docs/.memory/execution-memory.jsonl` 在上一次写入后仍未被 `doc-planner` 有效利用。
   - **Evidence**: 本轮仍无 planner 输出，直接进入 Stage 1。
   - **Impact**: 无法做变更级别预判，两轮均按最保守的 T3 全量执行。

### Executable Improvement Suggestions

| Category | Suggested Path | Change Point | Expected Benefit | Verification Method |
|----------|---------------|--------------|------------------|---------------------|
| Agent 配置 | `.claude/agents/codes-builder.yaml` | `effort: xhigh` → `effort: max` | 消除重复出现的 Stage 3 代理调用失败 | 连续两轮失败，修复后第三轮验证 |
| Agent 配置 | `.claude/agents/doc-architect.yaml` | `effort: xhigh` → `effort: max` | 同上 | 同上 |
| 执行记忆 | `docs/.memory/execution-memory.jsonl` | 确认 `execution-memory.js` 写入路径与 planner 读取路径一致 | 使 planner 能在未来提供变更级别建议 | 检查 `doc-planner` 的读取逻辑 |
| 快速路径 | `.claude/skills/generate-document/rules/workflow.md` | 当检测到完全新功能（无既有代码引用）时，允许 T2 快速路径 | 减少全新功能的文档生成时间 | 规则文件更新后，新功能验证 |

### Un-evidenced Hypotheses (Class C)

1. **Observer 中间件的单请求开销可能超过 1ms 目标** —— 取决于 Python 字典查找和 ContextVar 性能，需实际基准测试验证。
2. **`FastApiMCP` 的路由可能完全独立于 FastAPI 路由表** —— 基于文档和社区 issue 的推测，需实现阶段验证。

---

## Postscript: Future Planning & Improvements

1. **实现阶段跟踪**：在 `implement-code` 完成后，更新本报告的 Verification Results 和 Changed File List，替换为实际 git diff 数据。
2. **压测基线**：使用 `locust` 建立 Observer 启用前后的性能基线，验证单请求开销 < 1ms。
3. **MCP 兼容性验证**：专门测试 `FastApiMCP` 路由是否经过 Observer 中间件，若不通过则调整挂载策略。
4. **安全审计**：邀请安全团队对沙箱 allowlist 和拦截逻辑进行渗透测试。
5. **多实例扩展**：当 YiAi 扩展到多实例部署时，将固定窗口限流替换为 Redis 分布式限流。
