# YiAi-测试设计 — services-execution

> 受控模块执行器的测试设计。覆盖 executor.py 全部公共函数。
>
> **来源**：源码分析 `/rui doc --from-code services-execution`
> **证据等级**：B | **项目类型**：backend

---

## 测试用例

### TC1: execute_module — 白名单内同步函数

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP1–FP4 |
| 前置条件 | mock 模块在 EXEC_ALLOWLIST 中，函数为同步函数 |
| 输入 | execute_module("allowed.module", "fn", {"key": "val"}) |
| 预期 | 函数被调用；返回预期结果；_record_execution 被调用 |

### TC2: execute_module — 白名单外拒绝

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC2 |
| 关联 FP# | FP1 |
| 前置条件 | EXEC_ALLOWLIST 不含目标 |
| 输入 | execute_module("forbidden.module", "fn", {}) |
| 预期 | BusinessException(PERMISSION_DENIED, "Execution forbidden") |

### TC3: parse_parameters — 合法 JSON 字符串

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP3 |
| 输入 | parse_parameters('{"key": "val"}') |
| 预期 | {"key": "val"} |

### TC4: parse_parameters — 非法 JSON

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC3 |
| 关联 FP# | FP3 |
| 输入 | parse_parameters("not json") |
| 预期 | BusinessException(INVALID_PARAMS, "Invalid JSON") |

### TC5: parse_parameters — JSON 数组

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC3 |
| 关联 FP# | FP3 |
| 输入 | parse_parameters("[1,2,3]") |
| 预期 | BusinessException(INVALID_PARAMS, "must be a JSON object") |

### TC6: parse_parameters — dict 透传

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP3 |
| 输入 | parse_parameters({"key": "val"}) |
| 预期 | {"key": "val"}（原样返回） |

### TC7: _check_whitelist — 空参数

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP1 |
| 输入 | _check_whitelist("", "fn") |
| 预期 | BusinessException(INVALID_PARAMS, "Module path and function name required") |

### TC8: _check_whitelist — 通配符模式

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP1, R1 |
| 前置条件 | EXEC_ALLOWLIST = {"*"} |
| 输入 | _check_whitelist("any.module", "any_fn") |
| 预期 | 通过，不抛异常 |

### TC9: _import_target_function — 不存在模块

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP2 |
| 输入 | _import_target_function("nonexistent.module", "fn") |
| 预期 | BusinessException(INVALID_PARAMS, "Module or function not found") |

### TC10: _acquire_guard — 未启用

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP5 |
| 前置条件 | observer_guard_enabled=False |
| 输入 | _acquire_guard() |
| 预期 | 返回 None（守卫跳过） |

### TC11: _acquire_guard — 深度超限

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP5 |
| 前置条件 | 当前深度 >= max_depth |
| 输入 | _acquire_guard() |
| 预期 | BusinessException(SERVER_ERROR, "Reentrancy depth exceeds limit") |

### TC12: run_script — 成功执行

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC4 |
| 关联 FP# | FP7 |
| 前置条件 | mock subprocess 返回 returncode=0, stdout="ok" |
| 输入 | run_script("/path/to/script.py") |
| 预期 | {success: true, stdout: "ok", returncode: 0} |

### TC13: run_script — 超时

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC5 |
| 关联 FP# | FP7 |
| 前置条件 | mock subprocess 超时 |
| 输入 | run_script("/path/to/slow.py", timeout=1) |
| 预期 | process.kill() 被调用；返回 {success: false, message: "脚本执行超时"} |

### TC14: run_script — 非零返回码

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC4 |
| 关联 FP# | FP7 |
| 前置条件 | mock subprocess returncode=1, stderr="error" |
| 输入 | run_script("/path/to/fail.py") |
| 预期 | {success: false, stderr: "error", returncode: 1} |

### TC15: execute_module — 生成器函数

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP8 |
| 前置条件 | 目标函数为 async generator |
| 输入 | execute_module(..., stream_fn, ...) |
| 预期 | 返回生成器对象（不 await） |

### TC16: _record_execution — recorder 不可用

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP6, R3 |
| 前置条件 | _get_recorder() 返回 None |
| 输入 | _record_execution(...) |
| 预期 | 不抛异常，静默返回 |

---

## Gate A 交接信号

| 检查项 | 状态 |
|--------|:---:|
| AC 全覆盖 | ✓ (AC1–AC5) |
| 安全层测试 | ✓ (白名单/守卫/参数解析) |
| 降级路径 | ✓ (guard/recorder/sandbox disabled) |
| 脚本执行 | ✓ (成功/超时/失败) |

---

## 回溯链

| 来源 | 路径 |
|------|------|
| 故事任务 | `YiAi-故事任务.md` §5 |
| 源码 | `src/services/execution/executor.py` |

### 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2026-05-22 | 1.0.0 | 初始 /rui doc --from-code |
