# DevOps 文档

> 构建、部署与运维指南

---

## 构建

### 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | >= 3.10 | 运行环境 |
| MongoDB | >= 5.0 | 数据库服务 |
| Ollama | >= 0.1.0 | 本地 LLM 服务（可选） |

### 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖见 `requirements.txt`：
- fastapi>=0.104.0
- uvicorn>=0.24.0
- pydantic>=2.0.0
- motor>=3.3.0
- pymongo>=4.6.0
- PyYAML>=6.0
- oss2>=2.18.0
- aiohttp>=3.9.0
- feedparser>=6.0.10
- apscheduler>=3.10.0

### 本地启动

```bash
# 方式一：根入口
python main.py

# 方式二：模块方式
python -m src

# 方式三：uvicorn 直接启动
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## 部署

### 配置

编辑 `config.yaml` 或通过环境变量覆盖：

| 配置项 | 环境变量 | 说明 |
|--------|---------|------|
| server.host | SERVER_HOST | 监听地址 |
| server.port | SERVER_PORT | 监听端口 |
| mongodb.url | MONGODB_URL | MongoDB 连接字符串 |
| middleware.auth_enabled | MIDDLEWARE_AUTH_ENABLED | 是否启用认证 |
| middleware.auth_token | API_X_TOKEN | 认证令牌 |
| oss.* | OSS_* | 阿里云 OSS 配置 |
| ollama.url | OLLAMA_URL | Ollama 服务地址 |

### 生产部署建议

1. 禁用自动重载：`server.reload: false`
2. 启用认证：`middleware.auth_enabled: true`
3. 配置有效的 `API_X_TOKEN`
4. 使用 systemd 或 docker 管理服务
5. 配置日志轮转

## 运维

### 日常检查

| 检查项 | 命令/方法 |
|--------|----------|
| 服务状态 | `curl http://localhost:8000/docs` |
| MongoDB 连接 | 检查日志中的 "MongoDB connected" |
| RSS 调度器 | 检查日志中的调度器启动信息 |
| 磁盘空间 | 监控 `static.base_dir` 目录 |

### 日志

- 日志级别由 `config.yaml` 中 `logging.level` 控制
- Uvicorn 日志传播由 `logging.propagate_uvicorn` 控制
- 日志目录：`logs/`

### 常见问题

| 问题 | 排查 |
|------|------|
| 启动失败 | 检查 MongoDB 是否运行、端口是否被占用 |
| 模块执行失败 | 检查 `module.allowlist` 配置 |
| 文件上传失败 | 检查 `static.base_dir` 目录权限和 OSS 配置 |
| RSS 不更新 | 检查 `rss.scheduler_enabled` 和 `rss.scheduler_interval` |
