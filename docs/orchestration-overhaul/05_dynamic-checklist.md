# Orchestration Overhaul — Dynamic Checklist

> **Document Version**: v1.0 | **Last Updated**: 2026-05-03 | **Upstream**: [02 Requirement Tasks](./02_requirement-tasks.md), [03 Design Document](./03_design-document.md)
>

[General Checks](#general-checks) | [Scenario Verification](#scenario-verification) | [Feature Implementation](#feature-implementation) | [Code Quality](#code-quality) | [Testing](#testing) | [Check Summary](#check-summary)

---

## General Checks

| Check Item | Priority | Status | Notes |
|-----------|----------|--------|-------|
| Title format correct | P0 | ⏳ Pending | 标题使用 `# Feature Name — Document Type` |
| Linked document links valid | P0 | ⏳ Pending | 01→02→03→04 相互链接可点击 |
| Related files created/updated | P0 | ⏳ Pending | `src/services/orchestration/` 目录及文件已创建或计划创建 |
| Project buildable | P0 | ⏳ Pending | `python main.py` 可启动，无导入错误 |

---

## Scenario Verification

### S1: Submit and Execute a Pipeline

**Linked Requirement Tasks**: [02#S1](./02_requirement-tasks.md#scenario-s1-submit-and-execute-a-pipeline)
**Linked Design Document**: [03#S1](./03_design-document.md#scenario-s1-submit-and-execute-a-pipeline)
**Verification Tool Recommendation**: `pytest` + `fastapi.testclient.TestClient`

#### Preconditions Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| Orchestration 已启用 | P0 | ⏳ Pending | `config.yaml` 中 `orchestration_enabled=true` |
| State Store 可写入 | P0 | ⏳ Pending | Smoke test创建 state record 成功 |
| Launcher 已初始化 | P0 | ⏳ Pending | `/health/launcher` 返回 healthy=true |

#### Operation Steps Verification

| Step | Description | Priority | Status | Verification Method |
|------|-------------|----------|--------|---------------------|
| 1 | POST `/orchestration/pipelines` | P0 | ⏳ Pending | 返回 201 和 pipeline_id |
| 2 | 步骤含依赖，按拓扑序执行 | P0 | ⏳ Pending | 验证日志中的执行顺序 |
| 3 | Harness 为每步评分 | P0 | ⏳ Pending | `/state/records?record_type=audit_score` 有记录 |
| 4 | 评分在 0-100 之间 | P0 | ⏳ Pending | 断言 score 范围 |

#### Expected Results Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| 流水线完成 | P0 | ⏳ Pending | status == completed |
| 评分持久化 | P0 | ⏳ Pending | state_records 查询非空 |
| 相同定义多次执行结果一致 | P0 | ⏳ Pending | 两次 run 结果比对 |

#### Verification Focus Points

| Focus Point | Priority | Status | Verification Method |
|------------|----------|--------|---------------------|
| 拓扑序正确 | P1 | ⏳ Pending | 多依赖步骤在下游完成后才执行 |
| 步骤失败时流水线终止 | P1 | ⏳ Pending | Mock 模块抛异常，验证后续步骤未执行 |
| 评分确定性 | P1 | ⏳ Pending | 相同输入输出相同分数 |

---

### S2: Switch Launcher Mode

**Linked Requirement Tasks**: [02#S2](./02_requirement-tasks.md#scenario-s2-switch-launcher-mode)
**Linked Design Document**: [03#S2](./03_design-document.md#scenario-s2-switch-launcher-mode)
**Verification Tool Recommendation**: `pytest` + 配置覆盖

#### Preconditions Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| python3 可执行 | P0 | ⏳ Pending | `which python3` |
| 配置项存在 | P0 | ⏳ Pending | `config.yaml` 含 `orchestration_launcher_mode` |

#### Operation Steps Verification

| Step | Description | Priority | Status | Verification Method |
|------|-------------|----------|--------|---------------------|
| 1 | 修改配置为 subprocess | P0 | ⏳ Pending | 重启后 `/health/launcher` 返回 mode=subprocess |
| 2 | `/execution` 调用正常 | P0 | ⏳ Pending | 返回 200 且结果正确 |
| 3 | 修改配置为 direct | P0 | ⏳ Pending | 重启后 mode=direct |

#### Expected Results Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| 模式切换无 API 变更 | P0 | ⏳ Pending | 相同请求参数，两种模式结果一致 |
| subprocess 超时生效 | P1 | ⏳ Pending | Mock 慢模块，验证超时 kill |

#### Verification Focus Points

| Focus Point | Priority | Status | Verification Method |
|------------|----------|--------|---------------------|
| Launcher 失败时降级 | P1 | ⏳ Pending | Mock subprocess 失败，验证 fallback |
| 子进程环境隔离 | P1 | ⏳ Pending | 子进程修改全局变量不影响主进程 |

---

### S3: 5-Layer Loop Prevention Blocks Cyclic Pipeline

**Linked Requirement Tasks**: [02#S3](./02_requirement-tasks.md#scenario-s3-5-layer-loop-prevention-blocks-cyclic-pipeline)
**Linked Design Document**: [03#S3](./03_design-document.md#scenario-s3-5-layer-loop-prevention-blocks-cyclic-pipeline)
**Verification Tool Recommendation**: `pytest` + `TestClient`

#### Preconditions Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| DAGValidator 已启用 | P0 | ⏳ Pending | 配置 `orchestration_enabled=true` |
| ModuleGraphTracker 已启用 | P0 | ⏳ Pending | 配置 `observer_guard_enabled=true` |

#### Operation Steps Verification

| Step | Description | Priority | Status | Verification Method |
|------|-------------|----------|--------|---------------------|
| 1 | POST 含环流水线 | P0 | ⏳ Pending | 返回 400 |
| 2 | 错误信息包含环路径 | P0 | ⏳ Pending | 响应 body 包含 `A -> B -> A` |
| 3 | POST 自环流水线 | P0 | ⏳ Pending | 返回 400 |
| 4 | 运行时模块自调用 | P0 | ⏳ Pending | 返回 508 |

#### Expected Results Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| L5 拦截静态环 | P0 | ⏳ Pending | HTTP 400 |
| L4 拦截动态环 | P0 | ⏳ Pending | HTTP 508 |
| 不同请求互不干扰 | P0 | ⏳ Pending | 并发请求各自独立计数 |

#### Verification Focus Points

| Focus Point | Priority | Status | Verification Method |
|------------|----------|--------|---------------------|
| 复杂环检测 | P1 | ⏳ Pending | A→B→C→D→A 被检测 |
| 错误信息可读性 | P1 | ⏳ Pending | 非技术人员能理解环路径 |

---

### S4: Runtime Module Cycle Blocked by L4

**Linked Requirement Tasks**: [02#S4](./02_requirement-tasks.md#scenario-s4-runtime-module-cycle-blocked-by-l4)
**Linked Design Document**: [03#S4](./03_design-document.md#scenario-s4-runtime-module-cycle-blocked-by-l4)
**Verification Tool Recommendation**: `pytest` + Mock 回调

#### Preconditions Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| ModuleGraphTracker 已启用 | P0 | ⏳ Pending | 配置确认 |
| 合法流水线已提交 | P0 | ⏳ Pending | 201 创建成功 |

#### Operation Steps Verification

| Step | Description | Priority | Status | Verification Method |
|------|-------------|----------|--------|---------------------|
| 1 | 运行合法流水线 | P0 | ⏳ Pending | 返回 200 |
| 2 | 模块内部回调 /execution | P0 | ⏳ Pending | 深度超限返回 508 |
| 3 | 流水线终止 | P0 | ⏳ Pending | 状态为 failed |

#### Expected Results Verification

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| L4 拦截回调 | P0 | ⏳ Pending | HTTP 508 |
| ContextVar 隔离 | P0 | ⏳ Pending | 其他并发请求不受影响 |
| 异常后状态清理 | P1 | ⏳ Pending | 后续新请求正常执行 |

#### Verification Focus Points

| Focus Point | Priority | Status | Verification Method |
|------------|----------|--------|---------------------|
| Tracker 内存不泄漏 | P1 | ⏳ Pending | 长时间运行后内存平稳 |
| 调用链完整性 | P1 | ⏳ Pending | 508 响应包含完整调用链 |

---

## Feature Implementation Checks

### Core Features

| Check Item | Priority | Status | Linked Design Document Chapter |
|-----------|----------|--------|-------------------------------|
| PipelineEngine 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| DAGValidator 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| HarnessScorer 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| BaseLauncher 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| DirectLauncher 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| SubprocessLauncher 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| ModuleGraphTracker 实现 | P0 | ⏳ Pending | [03 Implementation Details](#implementation-details) |
| `/orchestration/pipelines` 路由 | P0 | ⏳ Pending | [03 Architecture Design](#architecture-design) |
| `/health/launcher` 扩展 | P1 | ⏳ Pending | [03 Architecture Design](#architecture-design) |
| `execute_module` 集成 Launcher | P0 | ⏳ Pending | [03 Changes](#changes) |
| `config.yaml` 默认配置 | P0 | ⏳ Pending | [03 Changes](#changes) |

### Boundary and Error Handling

| Check Item | Priority | Status | Linked Design Document Chapter |
|-----------|----------|--------|-------------------------------|
| Launcher 失败不穿透业务层 | P0 | ⏳ Pending | [03 Design Overview](#design-overview) |
| Harness 评分失败不影响执行 | P0 | ⏳ Pending | [03 Design Overview](#design-overview) |
| 400/508 响应格式符合规范 | P1 | ⏳ Pending | [03 Data Structure Design](#data-structure-design) |
| 配置缺失时使用安全默认值 | P1 | ⏳ Pending | [03 Implementation Details](#implementation-details) |

---

## Code Quality Checks

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| Style compliance (Ruff) | P1 | ⏳ Pending | `ruff check src/services/orchestration/` |
| Naming clarity | P1 | ⏳ Pending | 类名 CapWords，函数 snake_case |
| Type annotations coverage | P1 | ⏳ Pending | 所有公共函数参数和返回值有类型注解 |
| Performance (Kahn algorithm) | P2 | ⏳ Pending | 100 步 DAG 验证 < 10ms |
| Security risks | P0 | ⏳ Pending | SAST 扫描 launcher 和沙箱逻辑 |

---

## Testing Checks

| Check Item | Priority | Status | Verification Method |
|-----------|----------|--------|---------------------|
| Unit coverage core (orchestration/) | P1 | ⏳ Pending | `pytest tests/services/orchestration/` |
| E2E coverage main scenarios (S1-S4) | P0 | ⏳ Pending | `pytest tests/e2e/test_orchestration.py` |
| P0 tests all passed | P0 | ⏳ Pending | `pytest -m "p0"` 全部通过 |
| Test report complete | P1 | ⏳ Pending | `pytest --cov=src/services/orchestration --cov-report=html` |

---

## Check Summary

### Overall Progress

| Category | Total | Completed | Pass Rate |
|----------|-------|-----------|-----------|
| General Checks | 4 | 0 | 0% |
| Scenario Verification | 40 | 0 | 0% |
| Feature Implementation | 15 | 0 | 0% |
| Code Quality | 5 | 0 | 0% |
| Testing | 4 | 0 | 0% |
| **Total** | **68** | **0** | **0%** |

### Pending Items

- [ ] General Checks: 全部 4 项待验证
- [ ] S1 Verification: 全部 10 项待验证
- [ ] S2 Verification: 全部 8 项待验证
- [ ] S3 Verification: 全部 8 项待验证
- [ ] S4 Verification: 全部 8 项待验证
- [ ] Feature Implementation: 全部 15 项待编码验证
- [ ] Code Quality: 全部 5 项待检查
- [ ] Testing: 全部 4 项待执行

### Conclusion

⏳ 检查尚未开始。等待 `implement-code` 阶段完成后，根据实际代码和测试结果回填本清单。

---

## Postscript: Future Planning & Improvements

1. **自动化测试触发**：CI 中增加 orchestration 专项测试 stage。
2. **性能基线门禁**：DAG 验证耗时 > 10ms 则拒绝合并。
3. **混沌测试**：模拟 Launcher 失败，验证降级行为。
4. **覆盖率追踪**：`src/services/orchestration/` 测试覆盖率目标 90%。
5. **文档同步**：checklist 更新后自动触发 `import-docs`。
