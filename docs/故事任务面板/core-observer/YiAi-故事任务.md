# YiAi-故事任务 — core-observer

> Observer 可靠性子系统故事任务。覆盖限流(throttle)、采样(sampler)、沙箱(sandbox)、懒启动(lazy_start)、重入守卫(guard) 5 个组件。
>
> **来源**：源码分析 `/rui doc --from-code core-observer`
> **证据等级**：B（只读源码 + 静态分析）
> **项目类型**：backend

---

## 效果示意

```mermaid
flowchart LR
    NOW["当前状态<br/>Observer 子系统无文档"]:::pain
    NOW --> GOAL["目标状态<br/>5 组件可靠性模型清晰"]:::goal

    classDef pain fill:#ffebee,stroke:#c62828;
    classDef goal fill:#e8f5e9,stroke:#2e7d32;
```

---

## §1 Story

### Story 1: 请求限流（Throttle）

| 字段 | 内容 |
|------|------|
| 作为 | 系统运维人员 |
| 我想要 | 按客户端 IP 限制请求频率 |
| 以便 | 防止单客户端滥用导致服务过载 |
| 优先级 | P0 |
| 范围边界 | 固定窗口算法，按 IP 计数 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 正常请求 | 客户端未超限 | dispatch → 清理过期窗口 → 检查计数 → 更新计数 → 添加限流头 | 请求正常处理，响应含 X-RateLimit-* 头 |
| 2 | 超限拒绝 | 客户端超过 max_requests/窗口 | 返回 429 + Retry-After 头 + 限流信息 | JSON 错误响应 |
| 3 | 白名单豁免 | 客户端 IP 在白名单中 | 直接放行，不计数 | 请求正常处理 |
| 4 | 中间件异常 | dispatch 内部异常 | fail-closed：返回 500 | 不将异常请求放行 |

---

### Story 2: 慢请求采样（TailSampler）

| 字段 | 内容 |
|------|------|
| 作为 | 性能分析人员 |
| 我想要 | 只采集慢请求（>5s）和错误请求（≥500）的详细记录 |
| 以便 | 定位性能瓶颈而不消耗过多存储 |
| 优先级 | P1 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 记录慢请求 | 请求耗时 > slow_threshold_ms | start → finish → 入 ring buffer | 采样记录保存 |
| 2 | 记录错误请求 | status_code ≥ 500 | finish → 入 ring buffer | 错误请求始终采样 |
| 3 | 正常请求跳过 | 快请求 + 非错误 | finish 返回 False，不入 buffer | 节省存储 |
| 4 | 查询采样记录 | 调用 get_records() | 返回 buffer 中所有记录 | list[SampleRecord] |

---

### Story 3: 沙箱隔离（Sandbox）

| 字段 | 内容 |
|------|------|
| 作为 | 安全管理员 |
| 我想要 | 限制动态执行模块的文件系统和网络访问 |
| 以便 | 防止未授权的 I/O 操作 |
| 优先级 | P0 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 允许路径访问 | 文件路径在 fs_allowlist 中 | Path.resolve → is_relative_to → 放行 | open() 正常执行 |
| 2 | 拒绝路径访问 | 路径不在白名单 | SandboxViolation 异常 | 文件访问被阻断 |
| 3 | 网络检查 | host 在 network_allowlist 中（含子域名） | 精确匹配或 *.domain 匹配 | 通过或拒绝 |

---

### Story 4: 懒启动（LazyStart）

| 字段 | 内容 |
|------|------|
| 作为 | 系统架构师 |
| 我想要 | 重型 Observer 组件按需初始化而非启动时全部加载 |
| 以便 | 减少冷启动时间，按需分配资源 |
| 优先级 | P2 |

### Story 5: 重入守卫（ReentrancyGuard）

| 字段 | 内容 |
|------|------|
| 作为 | 系统可靠性保障 |
| 我想要 | 防止异步上下文中的递归调用导致栈溢出 |
| 以便 | 限制 execute_module 的最大嵌套深度 |
| 优先级 | P0 |

---

## §2 Requirements

### 功能点

| FP# | 描述 | 组件 | 优先级 |
|-----|------|------|:---:|
| FP1 | 固定窗口限流 — 按 IP 计数，超限返回 429 + Retry-After | throttle | P0 |
| FP2 | IP 白名单 — 白名单内 IP 不计入限流 | throttle | P1 |
| FP3 | 限流响应头 — X-RateLimit-Limit/Remaining/Reset | throttle | P1 |
| FP4 | Fail-closed — 限流器异常时返回 500 而非放行 | throttle | P0 |
| FP5 | 尾部采样 — 仅记录慢请求(>5s)和错误(≥500) | sampler | P1 |
| FP6 | Ring buffer — 固定大小 deque(maxlen=1000) | sampler | P1 |
| FP7 | 文件系统沙箱 — Path.resolve + is_relative_to + builtins.open monkey-patch | sandbox | P0 |
| FP8 | 网络检查 — 精确匹配 + *.domain 子域名匹配 | sandbox | P1 |
| FP9 | ContextVar 重入计数 — async/sync 双模式 guard 装饰器 | guard | P0 |
| FP10 | asyncio.Lock 双重检查 — 协程安全的懒初始化 | lazy_start | P2 |

### 业务规则

| R# | 描述 | 证据级别 |
|----|------|:---:|
| R1 | 限流器按 window_seconds 周期清理过期记录 | A |
| R2 | 沙箱 monkey-patch builtins.open，退出上下文时恢复原函数 | A |
| R3 | 沙箱 resolve 路径时先捕获 OSError/ValueError | A |
| R4 | 重入守卫 ContextVar 默认值 0，每个异步上下文独立 | A |
| R5 | SamplerMiddleware 在 finish 异常时不抛（logger.exception） | A |

---

## §3 成功标准

| SC# | 描述 | 优先级 |
|-----|------|:---:|
| SC1 | 客户端超限时收到 429 状态码和 Retry-After 头 | P0 |
| SC2 | 沙箱上下文内访问非白名单路径时抛 SandboxViolation | P0 |
| SC3 | 重入深度超限时抛 ReentrancyExceeded | P0 |
| SC4 | 慢请求被 TailSampler 捕获记录 | P1 |

---

## §4 范围边界

**范围内**：限流/采样/沙箱/重入守卫/懒启动 5 组件
**范围外**：分布式限流（当前单进程）、持久化采样记录

---

## §5 AC

| AC# | Given | When | Then | 门禁 |
|-----|-------|------|------|------|
| AC1 | 客户端在窗口内超过 max_requests | 发起第 max_requests+1 个请求 | 返回 429 + X-RateLimit-Remaining=0 | Gate A |
| AC2 | 文件路径不在 fs_allowlist | sandbox_context 内 open(path) | SandboxViolation | Gate A |
| AC3 | 深度=3，max_depth=3 | _acquire_guard() | ReentrancyExceeded | Gate A |
| AC4 | 请求耗时 6s | SamplerMiddleware.finish | 采样记录进入 buffer | Gate A |

---

### 主要价值

- 🛡️ **请求限流** — 固定窗口 + IP 白名单 + fail-closed 安全策略
- 🔍 **尾部采样** — 仅捕获慢/错请求，ring buffer 固定内存
- 🔒 **沙箱隔离** — builtins.open monkey-patch + 路径白名单 + 网络检查
- 🔄 **重入守卫** — ContextVar 隔离，async/sync 双模式

---

## 回溯链

| 来源 | 路径 | 证据级别 |
|------|------|---------|
| 源码 | `src/core/observer/` (5 文件) | A |
| 依赖 | `src/core/config.py` — observer_* 配置项 | B |

### 变更记录

| 日期 | 版本 | 变更内容 | 来源 |
|------|------|---------|------|
| 2026-05-22 | 1.0.0 | 初始文档基线 | /rui doc --from-code core-observer |
