# Security 文档

> 安全策略与威胁模型

---

## 安全架构

| 维度 | 措施 | 文件位置 |
|------|------|---------|
| 输入验证 | Pydantic 模型验证 + 参数校验 | `models/schemas.py`, `api/routes/*.py` |
| 路径安全 | 禁止 `..` 和绝对路径 | `api/routes/upload.py` (`_resolve_static_path`) |
| 认证 | 可选 X-Token 请求头认证 | `core/middleware.py` |
| 请求限流 | Observer ThrottleMiddleware，固定窗口 IP 限流 | `core/observer/throttle.py` |
| 执行沙箱 | Observer SandboxMiddleware，FS/网络访问控制 | `core/observer/sandbox.py` |
| 重入守卫 | Observer ReentrancyGuard，执行深度限制 | `core/observer/guard.py` |
| 错误处理 | 统一错误响应，不泄露内部细节 | `core/exception_handler.py` |
| 日志 | 请求和错误日志记录 | `core/logger.py`, `core/middleware.py` |
| CORS | 可配置跨域策略 | `src/main.py` |
| 依赖安全 | > 待补充（原因：未配置依赖安全扫描工具） |

## 威胁模型

| 威胁 | 风险等级 | 当前防护 | 建议 |
|------|---------|---------|------|
| 路径遍历 | 高 | `_resolve_static_path` 校验 | 定期审查文件操作接口 |
| 未授权访问 | 中 | 可选 X-Token 认证 | 生产环境强制启用认证 |
| SSRF（模块执行） | 高 | `module.allowlist` 白名单 | 生产环境禁用 `["*"]`，明确列出允许模块 |
| 敏感信息泄露 | 中 | 错误响应脱敏 | 避免在日志中记录敏感配置 |
| DoS | 中 | Observer ThrottleMiddleware 限流 + Uvicorn 并发限制 | 配置合理的 `throttle_max_requests` 和 `limit_concurrency` |
| 沙箱逃逸 | 高 | Observer SandboxMiddleware + `module.allowlist` | 启用 `sandbox_enabled`，审查 `sandbox_fs_allowlist` |
| 重入攻击 | 中 | Observer ReentrancyGuard（默认深度 3） | 根据业务调整 `guard_max_depth` |
| 注入攻击 | 低 | Pydantic 类型验证 | 保持模型验证严格 |

## 天检规则

| 检查项 | 检查方法 | 频率 |
|--------|---------|------|
| `module.allowlist` 不为 `["*"]` | 检查 `config.yaml` | 每次部署 |
| `middleware.auth_enabled` 在生产环境为 true | 检查 `config.yaml` | 每次部署 |
| 敏感配置不硬编码 | 代码审查 | 每次提交 |
| 文件路径安全校验 | 审查 `upload.py` | 每次变更 |
| 日志不包含敏感信息 | 日志审查 | 定期 |
| Observer `sandbox_enabled` 生产启用 | 检查 `config.yaml` | 每次部署 |
| Observer `guard_max_depth` 合理 | 检查 `config.yaml` | 每次部署 |

## 典型故障

| 故障 | 现象 | 根因 | 修复 |
|------|------|------|------|
| 路径遍历攻击 | 读取到非 static 目录文件 | 路径校验不完善 | 使用 `_resolve_static_path` 严格校验 |
| 模块执行滥用 | 执行了危险系统命令 | 白名单过宽 | 限制 `module.allowlist` 为具体模块 |
| 认证绕过 | 未传 Token 也能访问 | 白名单路径过多或认证未启用 | 审查白名单，生产启用认证 |
| 429 限流触发 | 正常请求被拦截 | IP 超过 `throttle_max_requests` | 调整限流参数或将 IP 加入 `throttle_whitelist` |
| 沙箱违规 | 模块执行中文件/网络访问被拒 | Sandbox 启用但 allowlist 不完整 | 审查 `sandbox_fs_allowlist` 和 `sandbox_network_allowlist` |

## 依赖审计

> 待补充（原因：未配置自动化依赖安全扫描工具，建议引入 `safety` 或 `pip-audit`）

手动检查方式：
```bash
pip list --outdated
```
