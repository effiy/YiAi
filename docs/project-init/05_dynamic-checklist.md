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
