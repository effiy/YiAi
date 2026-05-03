# FAQ 文档

> 常见问题与自愈参考

---

## 快速排查索引

| 症状 | 可能原因 | 排查命令 |
|------|---------|---------|
| 服务启动失败 | 依赖未安装 / 端口占用 | `pip install -r requirements.txt`, `lsof -i :8000` |
| MongoDB 连接超时 | 服务未启动 / 配置错误 | `systemctl status mongod`, 检查 `mongodb.url` |
| 401 未授权 | 认证中间件启用但未传令牌 | 检查请求头 `X-Token`，或禁用 `middleware.auth_enabled` |
| 模块执行 403 | 不在白名单中 | 检查 `module.allowlist` |
| 文件上传失败 | 目录权限 / OSS 配置 | `ls -la static/`, 检查 `oss.*` 配置 |
| RSS 不自动更新 | 调度器未启用 | 检查 `rss.scheduler_enabled` |
| Ollama 请求失败 | 服务未运行 | `curl http://localhost:11434/api/tags` |
| 静态文件 404 | 目录不存在 | `ls -la static/`, 检查 `static.base_dir` |
| 429 Too Many Requests | 触发限流 | 检查 `observer.throttle_max_requests`，或加 IP 到 `throttle_whitelist` |
| 状态记录写入失败 | State Store 未启用或 DB 故障 | 检查 `state_store.enabled` 和 MongoDB 连接 |
| CLI 命令报错 | State Store 服务无法访问 | 确认 `state_store.enabled: true`，MongoDB 运行中 |

## 问题分类

### 启动问题

**症状**：运行 `python main.py` 后报错退出

**排查步骤**：
1. 检查依赖：`pip install -r requirements.txt`
2. 检查端口占用：`lsof -i :8000` 或更换端口
3. 检查 MongoDB：`systemctl status mongod` 或 `mongosh`
4. 查看具体错误日志

**修复方案**：
- 依赖问题：重新安装 requirements
- 端口占用：修改 `config.yaml` 中 `server.port`
- MongoDB 未启动：启动 MongoDB 服务或修改连接地址

### 认证问题

**症状**：API 返回 401 或 403

**排查步骤**：
1. 确认 `middleware.auth_enabled` 配置
2. 确认请求头是否携带 `X-Token`
3. 确认 `API_X_TOKEN` 环境变量或 `middleware.auth_token` 配置值

**修复方案**：
- 开发环境：临时设置 `middleware.auth_enabled: false`
- 生产环境：在请求头中添加正确的 `X-Token`

### 文件操作问题

**症状**：上传/读取/删除文件失败

**排查步骤**：
1. 检查 `static.base_dir` 目录是否存在且有写入权限
2. 检查文件路径是否包含非法字符（`..`、绝对路径等）
3. 检查 OSS 配置（如果使用 OSS）

**修复方案**：
- 创建目录：`mkdir -p static && chmod 755 static`
- 检查路径：确保使用相对路径
- OSS 问题：检查 `oss.access_key`、`oss.secret_key`、`oss.bucket`、`oss.endpoint`

### 模块执行问题

**症状**：动态模块执行返回 403 或 422

**排查步骤**：
1. 确认模块路径和函数名正确
2. 确认 `module.allowlist` 包含该模块（或设为 `["*"]`）
3. 检查参数是否为有效的 JSON 对象

**修复方案**：
- 白名单问题：在 `config.yaml` 中添加模块到 `module.allowlist`
- 参数问题：确保 `parameters` 是合法的 JSON 字符串或字典

### RSS 问题

**症状**：RSS 源不更新或抓取失败

**排查步骤**：
1. 检查 `rss.scheduler_enabled` 是否为 `true`
2. 检查 `rss.scheduler_interval` 是否合理
3. 查看日志中的 RSS 相关错误

**修复方案**：
- 启用调度器：设置 `rss.scheduler_enabled: true`
- 手动触发：调用 `/execution` 执行 RSS 抓取模块

### AI 聊天问题

**症状**：Ollama 请求失败或返回错误

**排查步骤**：
1. 确认 Ollama 服务是否运行：`curl http://localhost:11434/api/tags`
2. 检查 `ollama.url` 配置
3. 检查模型是否已下载

**修复方案**：
- 启动 Ollama：`ollama serve`
- 下载模型：`ollama pull <model>`
- 修改配置：更新 `ollama.url`

### 限流问题

**症状**：API 返回 429 {"code":1003,"message":"Too Many Requests"}

**排查步骤**：
1. 检查当前 IP 是否触发了限流阈值
2. 查看 `observer.throttle_max_requests` 和 `observer.throttle_window_seconds` 配置
3. 检查 `observer.throttle_whitelist` 是否应加入当前 IP

**修复方案**：
- 调高 `throttle_max_requests`：增大窗口内允许的请求数
- 加入白名单：在 `throttle_whitelist` 中添加 IP 地址
- 临时关闭：设置 `observer.throttle_enabled: false`

### 状态记录问题

**症状**：状态记录 CRUD 操作失败或返回空

**排查步骤**：
1. 确认 `state_store.enabled: true`
2. 确认 MongoDB 连接正常
3. 检查 `collection_state_records` 对应的集合是否存在
4. 确认 `X-Token` 已携带（State 端点需认证）

**修复方案**：
- 启用服务：设置 `state_store.enabled: true`
- 检查权限：确认请求头包含有效 `X-Token`

## 自愈参考

| 场景 | 自动行为 | 需人工介入 |
|------|---------|-----------|
| OSS 上传失败 | 自动 fallback 到本地存储 | 检查 OSS 配置 |
| MongoDB 连接失败 | 启动时抛出异常，进程退出 | 检查 MongoDB 服务 |
| 参数验证失败 | 返回 400 和详细错误信息 | 修正请求参数 |
| 未捕获异常 | 返回 500 并记录错误日志 | 查看日志修复代码 |
| 请求过频（限流） | ThrottleMiddleware 返回 429，窗口过后自动恢复 | 降低请求频率或调整限流参数 |
| 沙箱违规 | SandboxMiddleware 抛出 SandboxViolation | 审查 fs/network allowlist |
