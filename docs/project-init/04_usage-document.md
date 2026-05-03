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
| `STATE_STORE_ENABLED` | `state_store.enabled` | `true` |
| `OBSERVER_ENABLED` | `observer.enabled` | `true` |
| `OBSERVER_THROTTLE_ENABLED` | `observer.throttle_enabled` | `true` |
| `OBSERVER_SANDBOX_ENABLED` | `observer.sandbox_enabled` | `false` |

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
7. 审查 Observer 配置（推荐生产环境启用 `sandbox_enabled`）

## 7. CLI 工具使用

```bash
# 列表查询（表格格式）
python src/cli/state_query.py list --record-type skill_execution

# JSON 格式输出
python src/cli/state_query.py list --format json --page-size 10

# 查看统计
python src/cli/state_query.py stats

# 获取单条记录
python src/cli/state_query.py get <record-key>

# 导出为文件
python src/cli/state_query.py export --output records.json
python src/cli/state_query.py export --format csv --output records.csv
```

## 8. State Store API 示例

```bash
# 创建状态记录（需认证）
curl -X POST http://localhost:8000/state/records \
  -H "Content-Type: application/json" \
  -H "X-Token: <your-token>" \
  -d '{"record_type":"audit","title":"测试记录","payload":{"action":"test"}}'

# 查询状态记录
curl "http://localhost:8000/state/records?record_type=audit&page_num=1&page_size=10" \
  -H "X-Token: <your-token>"

# 查看 Observer 健康状态
curl http://localhost:8000/health/observer -H "X-Token: <your-token>"
```

## Postscript: Future Planning & Improvements

- 补充 Docker / docker-compose 部署指南
- 补充 systemd 服务配置示例
- 补充 Nginx 反向代理配置

## Workflow Standardization Review

1. **Repetitive labor identification**: 配置示例在 usage-document 和 devops.md 中重复维护。
2. **Decision criteria missing**: 哪些配置项应出现在使用文档中（vs 仅保留在配置参考中）缺乏标准。
3. **Information silos**: CLI 使用说明和 State Store API 示例为新增内容，与现有文档的交叉引用不足。
4. **Feedback loop**: 配置变更后使用文档示例可能过时，缺乏自动检测。

## System Architecture Evolution Thinking

- **A1. Current architecture bottleneck**: 使用文档为静态文本，配置变化时无法自动更新。
- **A2. Next natural evolution node**: 从 config.yaml 自动生成配置参考表和示例。
- **A3. Risks and rollback plans for evolution**: 自动生成的文档可能丢失人工撰写的使用建议上下文。
