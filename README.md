# YiAi

AI 服务后端，基于 FastAPI + MongoDB + Ollama。

## 项目结构

```
YiAi/
├── main.py           # 入口
├── config.yaml       # 配置
├── src/
│   ├── main.py       # App 工厂
│   ├── api/routes/   # API 路由
│   ├── core/         # 核心模块
│   ├── models/       # 数据模型
│   └── services/     # 业务服务
├── static/           # 静态文件
└── tests/            # 测试
```

## 快速开始

```bash
pip install -r requirements.txt

# 编辑 config.yaml 配置 MongoDB 连接等参数
python main.py
# 服务启动在 http://0.0.0.0:10086
```

项目基线初始化：`/rui init`

## 系统能力

| 模块 | 功能 |
|------|------|
| 文件管理 | 上传/下载/删除/重命名，支持 Base64 编码，本地存储 + OSS 双通道 |
| AI 对话 | Ollama 模型对话接口 |
| RSS 调度 | 定时抓取 RSS 源，自动入库 |
| 动态执行 | 沙箱化的模块动态加载与执行 |
| 状态存储 | 键值状态持久化，支持 TTL |
| 企业微信 | 企业微信 Bot 回调处理 |
| Observer | 限流、采样、重入守卫、沙箱安全——运行时可靠性系统 |

## 技术栈

- **Web**: FastAPI + Uvicorn
- **数据库**: MongoDB (Motor 异步驱动)
- **配置**: YAML + Pydantic Settings
- **AI**: Ollama
- **任务调度**: APScheduler
- **对象存储**: Alibaba OSS

## 配置

编辑 `config.yaml`：

```yaml
server:
  host: "0.0.0.0"
  port: 10086

mongodb:
  url: "mongodb://localhost:27017"
  db_name: "ruiyi"

middleware:
  auth_enabled: true
  auth_token: "your-token"
```

所有配置项见 `config.yaml` 和 `src/core/config.py` 的 `Settings` 类。

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/upload-image-to-oss` | 图片上传 |
| POST | `/read-file` | 读取文件 |
| POST | `/write-file` | 写入文件 |
| POST | `/delete-file` | 删除文件 |
| POST | `/upload` | 文件上传 |
| GET | `/health/observer` | Observer 状态 |

## 认证

在请求头中携带 `X-Token`。默认 token 在 `config.yaml` 的 `middleware.auth_token` 配置。

## 开发

```bash
# 运行测试
python tests/smoke_observer.py

# 类型检查（如已配置）
mypy src/
```
