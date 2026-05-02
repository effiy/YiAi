# State Management 文档

> 状态管理约定与数据持久化

---

## 状态分类

| 状态类型 | 存储位置 | 生命周期 | 示例 |
|---------|---------|---------|------|
| 应用配置 | `config.yaml` + 环境变量 | 进程级 | 服务器端口、数据库地址 |
| 数据库连接 | `core.database.MongoDB` 单例 | 应用级 | MongoDB 客户端实例 |
| 运行时状态 | FastAPI 应用实例 / 内存 | 请求级 | 请求上下文、中间件状态 |
| 业务数据 | MongoDB 集合 | 持久化 | sessions、rss、chat_records |
| 静态文件 | 文件系统 (`static.base_dir`) | 持久化 | 上传的图片、文档 |

## 容器入口

### 配置访问

全局通过 `core.config.settings` 访问：
```python
from core.config import settings
port = settings.server_port
```

### 数据库访问

全局通过 `core.database.db` 访问：
```python
from core.database import db
await db.initialize()
collection = db.db[settings.collection_sessions]
```

## 读写边界

| 操作 | 推荐方式 | 禁止行为 |
|------|---------|---------|
| 读配置 | `settings.xxx` | 直接读取 `config.yaml` |
| 读数据库 | `db.db[collection].find_one()` | 绕过 `db` 单例新建连接 |
| 写数据库 | `db.insert_one()` / `db.insert_many()` | 不处理异常直接写入 |
| 文件操作 | `services/static/static_files.py` | 直接操作绝对路径 |

## 持久化

### MongoDB 持久化

- 数据库名由 `mongodb.db_name` 配置（默认 `ruiyi`）
- 自动创建 `createdTime` 字段
- RSS `link` 字段有唯一索引

### 文件持久化

- 本地静态文件存储在 `static.base_dir`
- OSS 配置有效时优先上传到云端
- 文件路径经过安全校验，禁止 `..` 和绝对路径

## 网络协作

- 无分布式状态共享（单实例部署）
- 如需多实例部署，需外部化 session 存储或引入 Redis

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 数据库未初始化 | 未调用 `db.initialize()` | 确保在 lifespan 中初始化或手动调用 |
| 配置未生效 | 环境变量格式错误 | 使用大写蛇形命名，如 `SERVER_HOST` |
| 文件路径越界 | 包含 `..` 或绝对路径 | 使用 `_resolve_static_path()` 安全解析 |
