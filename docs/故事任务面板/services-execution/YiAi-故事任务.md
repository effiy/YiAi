# YiAi-故事任务 — services-execution

> 受控模块执行器故事任务文档。覆盖 `executor.py`（白名单校验、沙箱隔离、重入守卫、执行记录）。
>
> **来源**：源码分析 `/rui doc --from-code services-execution`
> **证据等级**：B（只读源码 + 静态分析）
> **项目类型**：backend

---

## 效果示意

```mermaid
flowchart LR
    NOW["当前状态<br/>执行器无文档基线"]:::pain
    NOW --> M1["里程碑 1<br/>故事任务基线建立"]:::milestone
    M1 --> GOAL["目标状态<br/>执行器安全模型清晰"]:::goal

    classDef pain fill:#ffebee,stroke:#c62828;
    classDef milestone fill:#fff3e0,stroke:#e65100;
    classDef goal fill:#e8f5e9,stroke:#2e7d32;
```

---

## §1 Story

### Story 1: 受控模块执行

| 字段 | 内容 |
|------|------|
| 作为 | API 调用方 |
| 我想要 | 通过统一入口动态调用任意已注册模块的函数 |
| 以便 | 无需为每个模块编写独立 HTTP 路由 |
| 优先级 | P0 |
| 范围边界 | 仅执行白名单内的模块+函数组合，未注册的组合拒绝执行 |
| 依赖 | 目标模块可导入，白名单配置正确 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 调用模块函数 | GET/POST 传入 module_name + function_name + parameters | 白名单验证 → 参数解析 → 动态导入 → 沙箱执行 → 记录结果 | 返回函数执行结果 |
| 2 | 同步函数执行 | 目标为非异步函数 | 在白名单+沙箱上下文中直接调用 | 返回同步结果 |
| 3 | 异步函数执行 | 目标为 async 函数 | await 目标函数 | 返回异步结果 |
| 4 | 流式生成器执行 | 目标为 async generator / generator | 直接返回生成器对象（由调用方迭代） | 返回生成器对象 |

---

### Story 2: 安全隔离

| 字段 | 内容 |
|------|------|
| 作为 | 系统安全管理员 |
| 我想要 | 模块执行受到多层安全约束：白名单、重入深度限制、文件/网络沙箱 |
| 以便 | 防止未授权代码执行和资源滥用 |
| 优先级 | P0 |
| 范围边界 | 安全策略由配置和 Observer 组件控制 |
| 依赖 | Observer 子系统（sandbox / guard）已启用 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 白名单拒绝 | 模块+函数不在 EXEC_ALLOWLIST 中 | _check_whitelist 检测 → 抛出异常 | PERMISSION_DENIED |
| 2 | 重入深度超限 | 递归调用超过 max_depth | _acquire_guard 检测 → 抛出异常 | SERVER_ERROR(reentrancy) |
| 3 | 沙箱限制文件访问 | observer_sandbox_enabled=True | fs_allowlist / network_allowlist 生效 | 受限的 I/O 操作 |

---

### Story 3: 脚本执行

| 字段 | 内容 |
|------|------|
| 作为 | 运维人员或自动化任务 |
| 我想要 | 通过系统执行 Python 脚本并获取输出 |
| 以便 | 运行批处理任务或系统维护脚本 |
| 优先级 | P1 |
| 范围边界 | 默认 300s 超时，仅执行 Python3 脚本 |
| 依赖 | Python3 可用，脚本路径可访问 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 执行脚本 | 调用 run_script(path) | asyncio.create_subprocess_exec → 等待完成或超时 | 返回 {success, stdout, stderr, returncode} |
| 2 | 脚本超时 | 执行超时 | process.kill() → await process.wait() | 返回超时错误 |
| 3 | 脚本失败 | returncode != 0 | 记录 stderr → 返回失败结果 | 返回 {success: false, stderr} |

---

## §2 Requirements

### 功能点

| FP# | 描述 | 输入 | 输出 | 错误行为 | 优先级 |
|-----|------|------|------|---------|--------|
| FP1 | 白名单校验 — 验证 module:function 在 EXEC_ALLOWLIST 中 | module_path, function_name | 通过或异常 | 不在白名单 → PERMISSION_DENIED；空参数 → INVALID_PARAMS | P0 |
| FP2 | 动态导入 — importlib 加载模块 + getattr 获取函数 | module_path, function_name | 函数对象 | ImportError/AttributeError → INVALID_PARAMS | P0 |
| FP3 | 参数解析 — JSON string → dict 或直接透传 dict | parameters (dict/str) | Dict[str, Any] | 无效 JSON → INVALID_PARAMS；解析后非 dict → INVALID_PARAMS | P0 |
| FP4 | 沙箱执行 — 在 Observer sandbox_context 中运行函数 | target_function + params | 函数返回值 | 沙箱违反时 Observer 抛异常 | P0 |
| FP5 | 重入守卫 — ContextVar 深度计数，超限拒绝 | — | token 或异常 | 深度超限 → SERVER_ERROR | P1 |
| FP6 | 执行记录 — SkillRecorder 记录每次执行（best-effort） | 执行上下文 | 记录到 State Store | recorder 不可用/失败 → 静默跳过 | P1 |
| FP7 | 脚本执行 — asyncio subprocess + 超时 + kill | script_path + timeout | {success, stdout, stderr, returncode} | 超时 → kill 进程；非零返回码 → success=false | P1 |
| FP8 | 函数类型检测 — 区分 generator/asyncgen/coroutine/sync | target_function | 按类型调用 | — | P1 |

### 业务规则

| R# | 描述 | 校验方式 | 证据级别 |
|----|------|---------|---------|
| R1 | `*` 通配符在白名单中表示允许全部执行 | `_check_whitelist()`:183 — `if "*" not in EXEC_ALLOWLIST and allow_key not in ...` | A |
| R2 | 重入守卫和 SkillRecorder 均为懒加载，首次使用时才初始化 | `_get_recorder()` / `_get_guard()` — 全局变量 + None 检查 | A |
| R3 | 执行记录为 best-effort，失败不抛异常 | `_record_execution()`:215–216 — try/except + logger.error | A |
| R4 | 脚本执行默认超时 300s | `run_script()`:74 — `timeout: int = 300` | A |
| R5 | 白名单支持逗号分隔字符串或列表格式 | executor.py:22–24 — `isinstance(allowlist, str)` 分支 | A |
| R6 | 执行日志截断长度 500 字符 | `EXEC_LOG_TRUNCATION = 500` (:19) | A |

### 数据约束

| 约束 | 类型 | 范围/格式 | 来源 |
|------|------|----------|------|
| module_path | string | Python 模块路径如 `src.services.database.data_service` | `_import_target_function()` |
| function_name | string | 模块中可导出的函数名 | `_import_target_function()` |
| parameters | dict/str | JSON 对象字符串或 dict | `parse_parameters()` |
| timeout | int | 默认 300 秒 | `run_script()`:74 |
| max_depth | int | 配置 `observer_guard_max_depth` | `_get_guard()`:46 |

---

## §3 成功标准

| SC# | 描述 | 度量方式 | 目标值 | 优先级 | 关联 FP# |
|-----|------|---------|--------|--------|---------|
| SC1 | 白名单内模块函数可正常执行 | execute_module(allowed_module, allowed_fn, params) | 返回预期结果 | P0 | FP1, FP2, FP3 |
| SC2 | 白名单外模块函数被拒绝 | execute_module(not_allowed, fn, params) | PERMISSION_DENIED | P0 | FP1 |
| SC3 | 无效 JSON 参数被优雅拒绝 | execute_module(..., parameters="not json") | INVALID_PARAMS | P0 | FP3 |
| SC4 | 重入深度超限被拒绝 | 嵌套调用超过 max_depth | SERVER_ERROR | P1 | FP5 |

---

## §4 范围边界

### 范围内

| # | 条目 | 关联 FP# | 边界说明 |
|---|------|---------|---------|
| 1 | 受控模块调用 | FP1–FP5, FP8 | 白名单+沙箱+守卫+执行 |
| 2 | 脚本执行 | FP7 | subprocess + timeout |
| 3 | 执行记录 | FP6 | SkillRecorder best-effort |

### 范围外

| # | 条目 | 排除原因 |
|---|------|---------|
| 1 | 白名单的增删改 | 通过配置文件管理 |
| 2 | 沙箱策略定义 | 由 Observer 组件负责 |

---

## §5 AC

| AC# | Given | When | Then | 门禁 |
|-----|-------|------|------|------|
| AC1 | module+function 在白名单中 | 调用 execute_module(...) | 函数被正确导入并执行，结果返回 | Gate A |
| AC2 | module+function 不在白名单中 | 调用 execute_module(...) | PERMISSION_DENIED("Execution forbidden") | Gate A |
| AC3 | parameters 为非法 JSON 字符串 | parse_parameters("bad json") | INVALID_PARAMS | Gate A |
| AC4 | 脚本路径有效 | run_script(path) | 脚本执行并返回 stdout/stderr/returncode | Gate A |
| AC5 | 脚本执行超时 | run_script(path, timeout=1) | 进程被 kill，返回超时错误 | Gate A |

---

## §6 风险与假设

| # | 风险/假设 | 类型 | 可能性 | 影响 | 缓解策略 | 关联 FP# |
|---|----------|------|--------|------|---------|---------|
| 1 | 白名单配置错误导致关键功能瘫痪 | 风险 | L | H | `*` 通配符作为紧急恢复手段 | FP1 |
| 2 | 动态 import 被用于加载恶意模块 | 风险 | L | H | 白名单 + 沙箱双重限制；模块路径由服务端配置 | FP1, FP4 |
| 3 | asyncio.subprocess 命令注入 | 风险 | L | H | 使用 `create_subprocess_exec('python3', script_path)` 而非 shell 字符串 | FP7 |

---

### 主要价值

- 🔒 **四层安全防护** — 白名单 → 重入守卫 → 沙箱隔离 → 执行记录
- 🔌 **统一调用入口** — 所有模块通过同一 executor 动态调用，无需独立路由
- 📊 **全链路可观测** — SkillRecorder 记录每次执行状态/耗时/结果
- 🛡️ **沙箱隔离** — Observer fs_allowlist + network_allowlist 限制 I/O

---

## 回溯链

| 来源 | 路径 | 证据级别 |
|------|------|---------|
| 源码 | `src/services/execution/executor.py` (255 lines) | A |
| 依赖 | `src/core/config.py` — module_allowlist | B |
| 依赖 | `src/core/observer/` — sandbox / guard | B |

### 变更记录

| 日期 | 版本 | 变更内容 | 来源 |
|------|------|---------|------|
| 2026-05-22 | 1.0.0 | 初始文档基线，从源码反推生成 | /rui doc --from-code services-execution |
