# 项目初始化使用文档

> 环境搭建、配置指南与日常操作。

---

## 1. 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | >= 3.10 | 运行环境 |
| MongoDB | >= 5.0 | 数据库服务 |
| Ollama | >= 0.1.0 | 本地 LLM 服务（可选） |

## 2. 安装步骤

```bash
# 1. 克隆仓库
git clone <repository-url>
cd YiAi

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置
# 编辑 config.yaml，或设置环境变量

# 4. 启动
python main.py
```

## 3. 配置说明

### 3.1 基础配置（config.yaml）

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  reload: true

mongodb:
  url: "mongodb://localhost:27017"
  db_name: "ruiyi"

middleware:
  auth_enabled: true
  auth_token: "dev-token-change-me"

module:
  allowlist:
    - "*"
```

### 3.2 环境变量覆盖

| 环境变量 | 覆盖配置 | 示例 |
|----------|---------|------|
| `SERVER_HOST` | `server.host` | `0.0.0.0` |
| `SERVER_PORT` | `server.port` | `8000` |
| `MONGODB_URL` | `mongodb.url` | `mongodb://localhost:27017` |
| `API_X_TOKEN` | `middleware.auth_token` | `your-secure-token` |
| `OLLAMA_URL` | `ollama.url` | `http://localhost:11434` |

## 4. 启动方式

```bash
# 方式一：根入口（推荐）
python main.py

# 方式二：模块方式
python -m src

# 方式三：uvicorn 直接启动
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## 5. 验证启动

```bash
# 检查服务状态
curl http://localhost:8000/docs

# 检查健康（如启用了认证，需加 -H "X-Token: <token>"）
curl http://localhost:8000/execution?module_name=services.ai.chat_service&method_name=health_check
```

## 6. 生产部署建议

1. 禁用自动重载：`server.reload: false`
2. 启用认证：`middleware.auth_enabled: true`
3. 配置强 `API_X_TOKEN`
4. 限制 `module.allowlist`，不要使用 `["*"]`
5. 使用 systemd 或 docker 管理服务
6. 配置日志轮转

## Postscript: Future Planning & Improvements

- 补充 Docker / docker-compose 部署指南
- 补充 systemd 服务配置示例
- 补充 Nginx 反向代理配置
