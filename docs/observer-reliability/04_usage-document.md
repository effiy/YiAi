# Observer Reliability — Usage Document

> **Document Version**: v1.0 | **Last Updated**: 2026-05-03 | **Upstream**: [03 Design Document](./03_design-document.md)>

[Feature Intro](#feature-intro) | [Quick Start](#quick-start) | [Operation Scenarios](#operation-scenarios) | [FAQ](#faq) | [Tips](#tips)

---

## Feature Introduction

Observer Reliability 为 YiAi 提供了一套外围可靠性中间件，无需修改业务代码即可获得限流、采样、沙箱和重入防护能力。它以 FastAPI 中间件形式运行，覆盖 HTTP API、MCP 端点和动态模块执行。所有组件均可通过 `config.yaml` 独立开关和调参，适合需要快速加固现有服务稳定性的场景。

🎯 **即开即用**：修改配置即可启用限流和沙箱。

⚡ **低开销**：固定窗口限流 O(1)，采样使用预分配 ring buffer，守卫基于 ContextVar。

🔧 **故障隔离**：Observer 自身故障不会穿透到业务层。

**目标受众**：系统运维人员、后端开发者、安全工程师。

---

## Quick Start

### Prerequisites

- [ ] YiAi 服务已部署，FastAPI 可启动
- [ ] `config.yaml` 可编辑
- [ ] 了解现有路由和 MCP 工具清单

### 30-Second Onboarding

1. **启用 Observer**
   ```yaml
   # config.yaml
   observer_enabled: true
   observer_throttle_requests_per_second: 100
   observer_throttle_window_seconds: 60
   observer_sampler_buffer_size: 1000
   observer_sandbox_fs_allowlist:
     - /tmp
     - /var/www/YiAi/static
   observer_guard_max_depth: 3
   ```

2. **重启服务**
   ```bash
   python main.py
   ```

3. **查看健康状态**
   ```bash
   curl http://localhost:8000/health/observer
   ```

4. **测试限流**
   ```bash
   for i in {1..110}; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/execution; done
   ```
   最后几条应返回 `429`。

---

## Operation Scenarios

### Scenario 1: Enabling Rate Limiting for an API

**Applicable Situation**: 某个公开接口被高频调用，需要防止单客户端耗尽资源。

**Operation Steps**:
1. 编辑 `config.yaml`，设置 `observer_throttle_requests_per_second`。
2. 重启服务。
3. 观察日志中的 `Throttle:` 告警。

**Expected Results**: 超限客户端收到 429，响应头包含 `Retry-After`。

**Notes**:
- ✅ 限流按客户端 IP 计算，支持 IPv4 和 IPv6。
- ❌ 静态文件和白名单路径（如 `/mcp*`）默认不限流。

### Scenario 2: Investigating Slow Requests with Tail Sampling

**Applicable Situation**: 用户反馈偶发超时，需要定位慢请求根因。

**Operation Steps**:
1. 确保 `observer_sampler_buffer_size > 0`。
2. 等待慢请求发生。
3. 调用 `GET /health/observer`。
4. 查看 `sampler_buffer` 字段中的记录。

**Expected Results**: 返回的 JSON 包含慢请求的 path、duration_ms、status_code 和 request_id。

**Notes**:
- ✅ 所有 5xx 错误自动采样。
- ✅ 采样数据仅保存在内存，重启后丢失。
- ❌ 如需长期保留，需手动导出或等待 P2 持久化功能。

### Scenario 3: Adding a Sandbox Allowlist

**Applicable Situation**: 动态模块需要写入临时文件，但沙箱默认阻止所有写操作。

**Operation Steps**:
1. 确定模块需要访问的目录（如 `/tmp/my_module`）。
2. 在 `config.yaml` 的 `observer_sandbox_fs_allowlist` 中添加该路径。
3. 重启服务。
4. 测试模块执行。

**Expected Results**: 模块可正常读写 allowlist 内的路径；访问外部路径被阻止。

**Notes**:
- ✅ 路径支持前缀匹配，子目录自动允许。
- ✅ 符号链接会被解析为真实路径后再匹配。
- ❌ 沙箱仅对 `executor.py` 和 MCP 工具生效，不影响普通 API 路由。

### Scenario 4: Detecting Re-entrant Calls

**Applicable Situation**: 某模块回调 `/execution` 导致嵌套调用层数过多。

**Operation Steps**:
1. 确保 `observer_guard_max_depth` 已设置（默认 3）。
2. 触发模块执行。
3. 查看日志中的 `ReentrancyExceeded` 告警。
4. 根据 request_id 追踪调用链。

**Expected Results**: 超过深度限制的嵌套调用收到 508，外层调用不受影响。

**Notes**:
- ✅ 深度按异步上下文隔离，不同客户端并发不互相影响。
- ✅ 可在 `config.yaml` 中为特定路由单独配置深度限制。
- ❌ 守卫不阻止合法的异步并发，只阻止同上下文内的递归。

### Scenario 5: Disabling Observer for Maintenance

**Applicable Situation**：需要临时关闭 Observer 以排查问题。

**Operation Steps**：
1. 编辑 `config.yaml`，设置 `observer_enabled: false`。
2. 重启服务。
3. 确认 `/health/observer` 返回所有组件 disabled。

**Expected Results**：请求不再经过限流、沙箱和守卫，但业务逻辑正常。

**Notes**：
- ✅ 支持单个组件关闭（如仅关闭 throttle）。
- ❌ 关闭沙箱会降低安全性，建议仅在可控环境临时操作。

---

## FAQ

### 💡 Basics

**Q1: Observer 会影响现有 API 性能吗？**

A: 设计目标是单请求开销 < 1ms。限流和守卫是 O(1) 操作；采样仅在请求结束时做一次判断；沙箱仅在 `executor.py` 和 MCP 路径生效。

**Q2: 如何知道 Observer 是否已生效？**

A: 访问 `/health/observer`，如果组件状态为 `enabled` 且有运行时数据（如 `throttle_active_ips`），则表示已生效。

**Q3: 配置修改后需要重启吗？**

A: 当前版本需要重启（P1 规划支持热重载）。重启后新配置生效。

### ⚙️ Advanced

**Q4: 限流的“客户端”是如何识别的？**

A: 默认使用 `request.client.host`（IP 地址）。如果部署在反向代理后，可能需要从 `X-Forwarded-For` 读取真实 IP（P1 支持）。

**Q5: 采样数据如何导出？**

A: 目前只能通过 `/health/observer` 查看内存中的 buffer。未来版本支持导出到文件或 MongoDB。

**Q6: 沙箱能阻止所有恶意操作吗？**

A: 不能。当前实现是轻量级 allowlist，主要阻止文件系统和网络访问。对于 CPU/内存型攻击，需要结合容器或 gVisor 等更强隔离。

### 🔧 Troubleshooting

**Q7: 客户端收到 429，但认为自己没有发送很多请求。**

A: 检查是否多个客户端共享同一出口 IP（如 NAT）。如果是，考虑提高阈值或为该 IP 加入白名单。

**Q8: 模块在沙箱内无法读取自己的数据文件。**

A: 将数据文件所在目录加入 `observer_sandbox_fs_allowlist`。注意路径必须使用绝对路径。

**Q9: `/health/observer` 返回 404。**

A: 确认 `observer_enabled` 为 true 且服务已重启。如果仍不存在，检查 `main.py` 中是否注册了 observer 路由。

**Q10: 收到 508 Loop Detected，但代码中没有明显递归。**

A: 检查是否使用了异步回调或事件触发器，它们可能在同一 Task 中形成隐式调用链。增加 `observer_guard_max_depth` 或重构代码消除回调循环。

---

## Tips and Hints

### 💡 Practical Tips

1. **渐进启用**：先仅启用限流和采样，观察一周后再启用沙箱和守卫，降低风险。
2. **白名单优先**：在限流配置中为内部监控和健康检查 IP 设置白名单，避免误伤。
3. **采样配合日志**：tail sample 中的 `request_id` 可与应用程序日志关联，实现全链路追踪。

### ⌨️ Shortcuts

- `curl -s http://localhost:8000/health/observer | jq .` 快速查看状态。
- `grep "Throttle:" logs/app.log | tail -20` 查看最近限流记录。

### 📚 Best Practices

1. ** allowlist 最小化**：仅添加模块确实需要的路径，定期审计 allowlist。
2. **深度限制保守**：`observer_guard_max_depth` 建议保持在 3-5，超过此范围的调用链通常意味着设计问题。
3. **监控内存**：即使 Observer 本身内存有界，也应定期通过 `/health/observer` 检查采样 buffer 和限流表的大小趋势。

---

## Appendix

### Command Cheat Sheet

| Command | Description |
|---------|-------------|
| `curl http://localhost:8000/health/observer` | 查看 Observer 运行时状态 |
| `curl -I http://localhost:8000/execution` | 检查限流头（429 时含 Retry-After） |
| `grep "SandboxViolation" logs/app.log` | 查看沙箱拦截记录 |
| `grep "ReentrancyExceeded" logs/app.log` | 查看重入告警 |

### Related Resources

- [Design Document](./03_design-document.md)
- [Requirement Tasks](./02_requirement-tasks.md)
- [State Management](../state-management.md)
- [Security](../security.md)

---

## Postscript: Future Planning & Improvements

1. **热重载**：支持通过 SIGHUP 或 API 调用重载 Observer 配置，无需重启服务。
2. **IP 白名单动态管理**：提供 `/admin/observer/whitelist` 接口，运行时增删 IP。
3. **采样可视化**：在 `/health/observer` 返回直方图和百分位数据。
4. **沙箱策略 DSL**：用 JSON Schema 定义复杂策略（时间窗口、用户角色、文件类型）。
5. **Guard Call Graph**：导出模块调用关系图到 Graphviz，辅助重构递归逻辑。
