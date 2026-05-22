# YiAi-测试设计 — core-observer

> Observer 可靠性子系统测试设计。5 组件 22 用例。
>
> **来源**：源码分析 | **证据等级**：B | **项目类型**：backend

---

## 测试用例

### TC1–TC6: ThrottleMiddleware

| TC# | 场景 | 预期 |
|-----|------|------|
| TC1 | 正常请求（未超限） | 请求通过，响应头含 X-RateLimit-* |
| TC2 | 超限拒绝 | 429 + Retry-After + X-RateLimit-Remaining=0 |
| TC3 | 白名单 IP 豁免 | 不计入限流，正常通过 |
| TC4 | 窗口过期后恢复 | 旧窗口过期后计数重置 |
| TC5 | 中间件异常 fail-closed | 返回 500 而非放行 |
| TC6 | 窗口清理 | 过期条目被移除 |

### TC7–TC11: TailSampler

| TC# | 场景 | 预期 |
|-----|------|------|
| TC7 | 慢请求采样 | duration > 5s → 入 buffer |
| TC8 | 错误请求采样 | status >= 500 → 入 buffer |
| TC9 | 快请求跳过 | 快速 + 非错误 → 不入 buffer |
| TC10 | Ring buffer 溢出 | 超过 max_size 时最旧记录被覆盖 |
| TC11 | start 后无 finish | _starts 残留不影响后续 |

### TC12–TC16: Sandbox

| TC# | 场景 | 预期 |
|-----|------|------|
| TC12 | 白名单路径正常 open | 文件正常打开 |
| TC13 | 非白名单路径拒绝 | SandboxViolation |
| TC14 | 路径穿越拒绝 (../) | Path.resolve → is_relative_to 检测 |
| TC15 | 上下文退出恢复 | builtins.open 恢复原函数 |
| TC16 | 无效路径抛异常 | SandboxViolation("cannot resolve") |

### TC17–TC19: ReentrancyGuard

| TC# | 场景 | 预期 |
|-----|------|------|
| TC17 | 正常深度递增 | 1→2→3 正常执行 |
| TC18 | 深度超限 | ReentrancyExceeded |
| TC19 | 退出恢复深度 | finally 中 reset(token) 生效 |

### TC20–TC22: LazyStartManager

| TC# | 场景 | 预期 |
|-----|------|------|
| TC20 | 首次初始化 | init_func 被调用 |
| TC21 | 重复 ensure 幂等 | 仅初始化一次 |
| TC22 | init_func 未设置 | 返回 False |

---

## Gate A 交接信号

| 检查项 | 状态 |
|--------|:---:|
| AC 全覆盖 (AC1–AC4) | ✓ |
| 限流 fail-closed 测试 | ✓ (TC5) |
| 沙箱路径穿越测试 | ✓ (TC14) |
| 重入守卫深度测试 | ✓ (TC17–TC19) |

---

### 主要价值

- ✅ **22 用例覆盖 5 组件**
- 🛡️ **安全路径充分** — 限流 fail-closed / 沙箱路径穿越 / 守卫深度限制

---

## 回溯链

| 来源 | 路径 |
|------|------|
| 故事任务 | `YiAi-故事任务.md` §5 |
| 源码 | `src/core/observer/` |

### 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2026-05-22 | 1.0.0 | 初始 /rui doc --from-code |
