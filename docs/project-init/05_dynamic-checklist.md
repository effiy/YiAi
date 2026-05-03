# 项目初始化动态检查清单

> 可验证的检查项，用于确认项目初始化完成质量。

---

## P0 检查项（阻塞项）

### 环境启动

- [ ] `pip install -r requirements.txt` 执行成功，无依赖冲突
- [ ] `python main.py` 能正常启动，监听 `0.0.0.0:8000`
- [ ] `/docs` 可访问并显示 Swagger UI
- [ ] `/redoc` 可访问并显示 ReDoc 文档

### 数据库连接

- [ ] MongoDB 连接成功，日志中出现 "数据库初始化成功"
- [ ] 数据库集合能正常创建和访问

### 核心功能可用

- [ ] `/execution` GET 和 POST 能调用白名单模块
- [ ] 模块执行返回正确的 `StandardResponse` 格式
- [ ] 不在白名单的模块返回 403

### 配置系统

- [ ] `config.yaml` 中的配置生效
- [ ] 环境变量能正确覆盖 YAML 配置
- [ ] 未配置的必填项有合理的默认值或明确报错

## P1 检查项（重要项）

### 认证中间件

- [ ] `auth_enabled: true` 时，未携带 `X-Token` 返回 401
- [ ] 携带正确 `X-Token` 后请求正常通过
- [ ] 白名单路径（`/upload`, `/static/*`, `/mcp*`）无需认证
- [ ] `auth_enabled: false` 时所有请求放行

### 文件操作

- [ ] `/upload` 能上传文件到本地或 OSS
- [ ] `/read-file` 能读取已上传的文件
- [ ] `/delete-file` 能删除文件
- [ ] 路径包含 `..` 或绝对路径时被拒绝

### RSS 调度

- [ ] `rss.scheduler_enabled: true` 时调度器启动
- [ ] 定时抓取任务按 `rss.scheduler_interval` 间隔执行

### MCP 服务

- [ ] `/mcp` 路径可访问
- [ ] MCP 服务器正确挂载，不与 Maintenance 端点冲突

### State Store

- [ ] POST `/state/records` 创建记录成功，返回 `{"key": "..."}`
- [ ] GET `/state/records?record_type=X` 返回分页结果
- [ ] GET `/state/records/{key}` 返回单条记录
- [ ] PUT `/state/records/{key}` 更新记录成功
- [ ] DELETE `/state/records/{key}` 删除记录成功
- [ ] 不存在的 key 返回 404
- [ ] `state_records` 集合在 MongoDB 中自动创建

### Observer Reliability

- [ ] `GET /health/observer` 返回 Observer 各组件状态
- [ ] 超过 `throttle_max_requests` 后返回 429，`code: 1003`
- [ ] `throttle_whitelist` 中 IP 不受限流
- [ ] `observer.enabled: false` 时 Observer 健康端点仍可访问
- [ ] SamplerMiddleware 记录慢请求到环形缓冲区

### CLI 工具

- [ ] `python src/cli/state_query.py list` 表格格式正常输出
- [ ] `python src/cli/state_query.py list --format json` JSON 格式输出
- [ ] `python src/cli/state_query.py get <key>` 返回记录或 "Record not found"
- [ ] `python src/cli/state_query.py stats` 显示总数统计
- [ ] `python src/cli/state_query.py export -o out.json` 导出成功

## P2 检查项（优化项）

- [ ] 日志目录 `logs/` 正常生成，格式符合配置
- [ ] Uvicorn 并发限制生效
- [ ] CORS 配置正确响应预检请求
- [ ] 静态文件目录存在且有读取权限
- [ ] 错误响应不泄露内部堆栈细节

## Postscript: Future Planning & Improvements

- 增加自动化测试覆盖检查
- 增加依赖安全扫描检查
- 增加性能基准测试检查

## Workflow Standardization Review

1. **Repetitive labor identification**: P0/P1 检查项与 02 用户故事的验收标准高度重叠。
2. **Decision criteria missing**: 检查项分级（P0/P1/P2）的边界（如"功能不可用"vs"性能下降"）缺乏量化标准。
3. **Information silos**: 检查项分散在 05 和各 feature 文档中，缺乏统一的跟踪系统。
4. **Feedback loop**: 检查结果缺乏向相关文档章节的自动反馈。

## System Architecture Evolution Thinking

- **A1. Current architecture bottleneck**: 检查清单为静态 Markdown，无法追踪执行状态和历史趋势。
- **A2. Next natural evolution node**: 将检查清单集成为可执行的自动化测试套件，结果关联到文档。
- **A3. Risks and rollback plans for evolution**: 自动化测试可能因环境差异产生假阳性。回退：保持手动清单为权威参考。
