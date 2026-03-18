# 架构设计

本文档详细介绍 YiAi 项目的关键架构设计和实现模式。

## 🏗️ 整体架构

YiAi 采用经典的分层架构设计，从上到下依次为：

```
┌─────────────────────────────────────────────────┐
│                   API 层                        │
│            (api/routes/*.py)                    │
├─────────────────────────────────────────────────┤
│                  业务逻辑层                      │
│             (services/*/)                        │
├─────────────────────────────────────────────────┤
│                  核心基础设施层                  │
│               (core/*/)                          │
├─────────────────────────────────────────────────┤
│                  数据模型层                      │
│               (models/*/)                        │
└─────────────────────────────────────────────────┘
```

### 层级职责

- **API 层**：负责处理 HTTP 请求、参数验证、响应格式化
- **业务逻辑层**：实现核心业务功能，如文件上传、AI 聊天、RSS 抓取等
- **核心基础设施层**：提供配置、数据库、日志、异常处理等基础服务
- **数据模型层**：定义 Pydantic 数据模型和数据库集合结构

---

## 🔑 关键架构模式

### 1. 模块执行引擎

模块执行引擎是 YiAi 最核心的扩展机制，允许通过 REST API 动态执行 Python 模块方法。

#### 设计目标
- 提供最大的灵活性，允许在不修改 API 层的情况下扩展功能
- 支持多种函数类型（同步/异步、生成器等）
- 保证安全性，通过白名单控制可执行的模块
- 提供良好的用户体验，自动适配不同的函数类型

#### 实现原理

##### 函数类型检测
执行引擎会自动检测被调用函数的类型，并选择合适的执行方式：

```python
# 函数类型判断逻辑
if inspect.iscoroutinefunction(func):
    # 异步函数，直接 await
    result = await func(**params)
elif inspect.isasyncgenfunction(func):
    # 异步生成器，逐个 yield
    async for item in func(**params):
        yield item
elif inspect.isgeneratorfunction(func):
    # 同步生成器，逐个 yield
    for item in func(**params):
        yield item
else:
    # 普通同步函数，直接调用
    result = func(**params)
```

##### SSE 流式响应
对于生成器函数，执行引擎会自动使用 Server-Sent Events (SSE) 协议进行流式响应：

```
data: {"chunk": "第1部分数据"}

data: {"chunk": "第2部分数据"}

data: {"done": true}
```

#### 配置方式
在 `config.yaml` 中配置模块白名单：

```yaml
module:
  allowlist:
    - "services.storage.oss_client"
    - "services.rss.scheduler"
    # 或使用 "*" 允许所有模块
    # - "*"
```

#### 使用示例

**通过 API 调用：**
```bash
# GET 请求
GET /execution?module_name=services.storage.oss_client&method_name=list_files&parameters={"directory": "images/"}

# POST 请求
POST /execution
{
  "module_name": "services.storage.oss_client",
  "method_name": "list_files",
  "parameters": {"directory": "images/"}
}
```

**在代码中直接调用：**
```python
from services.execution.executor import execute_module

result = await execute_module(
    module_path="services.storage.oss_client",
    function_name="list_files",
    parameters={"directory": "images/"}
)
```

#### 相关文件
- `src/services/execution/executor.py` - 执行引擎核心实现
- `src/api/routes/execution.py` - API 端点包装

---

### 2. 配置系统

YiAi 使用 Pydantic Settings 实现灵活的配置管理，支持 YAML 配置文件和环境变量覆盖。

#### 设计目标
- 支持结构化的 YAML 配置文件
- 允许通过环境变量覆盖配置（便于容器化部署）
- 类型安全，使用 Pydantic 进行配置验证
- 全局单例访问，避免重复加载

#### 实现原理

##### YAML 配置加载
配置系统首先从 `config.yaml` 加载配置：

```yaml
server:
  host: "0.0.0.0"
  port: 8000

mongodb:
  url: "mongodb://localhost:27017"
  db_name: "ruiyi"
```

##### 环境变量覆盖
嵌套的 YAML 键会被扁平化为蛇形命名（snake_case），然后可以通过对应的大写环境变量覆盖：

| YAML 路径 | 环境变量名 | 示例 |
|-----------|-----------|------|
| `server.host` | `SERVER_HOST` | `SERVER_HOST=127.0.0.1` |
| `mongodb.url` | `MONGODB_URL` | `MONGODB_URL=mongodb://user:pass@host:27017` |
| `oss.access_key` | `OSS_ACCESS_KEY` | `OSS_ACCESS_KEY=your-access-key` |

##### Pydantic Settings 集成
配置类使用 Pydantic Settings 实现：

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 服务器配置
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    # MongoDB 配置
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "ruiyi"

    class Config:
        env_file = ".env"
        case_sensitive = False

# 全局单例
settings = Settings()
```

#### 使用方式

**在代码中访问配置：**
```python
from core.config import settings

# 访问配置
print(settings.server_host)
print(settings.mongodb_db_name)
```

#### 相关文件
- `src/core/config.py` - 配置管理实现

---

### 3. 数据库单例模式

YiAi 使用 Motor 异步驱动连接 MongoDB，并采用单例模式确保全局只有一个数据库连接实例。

#### 设计目标
- 异步非阻塞 I/O，提高并发性能
- 全局单例，避免重复创建连接
- 自动重连机制
- 生命周期管理（应用启动时连接，关闭时断开）

#### 实现原理

##### 单例实现
使用模块级别的全局变量实现单例：

```python
# src/core/database.py
from motor.motor_asyncio import AsyncIOMotorClient

# 全局数据库实例
_db = None

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def initialize():
    """初始化数据库连接"""
    global _db
    if db.client is None:
        db.client = AsyncIOMotorClient(settings.mongodb_url)
        db.db = db.client[settings.mongodb_db_name]
```

##### 生命周期管理
在 FastAPI 的 lifespan 事件中管理数据库连接：

```python
# src/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    await db.initialize()
    yield
    # 关闭时
    if db.client:
        db.client.close()
```

##### 数据访问
提供简洁的数据访问方法：

```python
async def find_one(collection_name: str, query: dict):
    """查询单条记录"""
    return await db.db[collection_name].find_one(query)

async def find_many(collection_name: str, query: dict, limit: int = 100):
    """查询多条记录"""
    cursor = db.db[collection_name].find(query)
    return await cursor.to_list(length=limit)

async def insert_one(collection_name: str, document: dict):
    """插入单条记录"""
    result = await db.db[collection_name].insert_one(document)
    return result.inserted_id
```

#### 使用方式

**在业务逻辑中使用：**
```python
from core.database import db

# 先确保初始化
await db.initialize()

# 查询数据
result = await db.find_one("sessions", {"user_id": "123"})

# 插入数据
await db.insert_one("chat_records", {"user_id": "123", "message": "hello"})
```

#### 相关文件
- `src/core/database.py` - 数据库单例和访问方法

---

### 4. 生命周期管理

YiAi 使用 FastAPI 的 lifespan 上下文管理器来管理应用的启动和关闭流程。

#### 设计目标
- 统一管理应用启动和关闭时的资源
- 确保资源正确初始化和释放
- 支持优雅关闭

#### 实现原理

```python
# src/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ==================== 启动阶段 ====================
    logger.info("应用启动中...")

    # 1. 初始化数据库连接
    if settings.startup_init_database:
        await db.initialize()
        logger.info("数据库连接已初始化")

    # 2. 启动 RSS 调度器
    if settings.startup_init_rss_system and settings.rss_scheduler_enabled:
        scheduler.start()
        logger.info("RSS 调度器已启动")

    logger.info("应用启动完成")

    yield  # 应用运行期间

    # ==================== 关闭阶段 ====================
    logger.info("应用关闭中...")

    # 1. 停止 RSS 调度器
    if settings.rss_scheduler_enabled:
        scheduler.stop()
        logger.info("RSS 调度器已停止")

    # 2. 关闭数据库连接
    if db.client:
        db.client.close()
        logger.info("数据库连接已关闭")

    logger.info("应用已关闭")
```

#### 启动任务配置
在 `config.yaml` 中可以配置启动时需要执行的任务：

```yaml
startup:
  init_database: true      # 是否初始化数据库
  init_rss_system: true    # 是否初始化 RSS 系统
```

#### 相关文件
- `src/main.py` - FastAPI 应用工厂和生命周期管理

---

### 5. 双重存储策略

文件上传功能支持 OSS 云存储和本地静态存储两种模式，自动 fallback。

#### 设计目标
- 优先使用 OSS 云存储，提供高可用性
- 当 OSS 未配置时，自动使用本地存储作为 fallback
- 对调用方透明，无需关心底层存储实现
- 保持 API 接口一致性

#### 实现原理

##### OSS 配置检测
在 `OSSConfig` 类中检测配置是否完整：

```python
class OSSConfig:
    def __init__(self):
        self.access_key_id = settings.oss_access_key
        self.access_key_secret = settings.oss_secret_key
        self.endpoint = settings.oss_endpoint
        self.bucket_name = settings.oss_bucket

        if not all([self.access_key_id, self.access_key_secret,
                    self.endpoint, self.bucket_name]):
            logger.warning("OSS config incomplete.")
```

##### 自动 fallback 逻辑
在 API 层实现 try-except fallback 机制：

```python
@router.post("/upload-image-to-oss")
async def upload_image_to_oss(request: ImageUploadToOssRequest):
    # 解码 base64 数据...

    # 尝试 OSS 上传
    try:
        result = await upload_bytes_to_oss(content, filename, directory=directory)
        return success(data=result)
    except Exception as e:
        # OSS 失败，fallback 到本地存储
        logger.warning(f"OSS upload failed, falling back to local storage: {e}")
        result = await _upload_to_local_storage(content, filename, directory)
        return success(data=result)
```

##### 本地存储实现
本地存储使用配置的 `static.base_dir` 和 `static.base_url`：

```python
async def _upload_to_local_storage(content: bytes, filename: str, directory: str) -> dict:
    # 生成唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}{file_ext}"

    # 构建路径
    rel_path = f"{directory}/{unique_filename}"
    abs_path = os.path.join(settings.static_base_dir, rel_path)

    # 写入文件
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(content)

    # 构建访问 URL
    static_url = f"{settings.static_base_url.rstrip('/')}/{rel_path}"

    return {
        "url": static_url,
        "filename": safe_filename,
        "object_name": rel_path
    }
```

#### 配置项

**OSS 配置（可选）：**
```yaml
oss:
  access_key: "your-access-key"
  secret_key: "your-secret-key"
  endpoint: "oss-cn-hangzhou.aliyuncs.com"
  bucket: "your-bucket-name"
```

**本地存储配置（必需）：**
```yaml
static:
  base_dir: "/var/www/YiKnowledge/static"
  base_url: "https://api.effiy.cn/static"
```

#### 相关文件
- `src/api/routes/upload.py` - 上传端点和 fallback 逻辑
- `src/services/storage/oss_client.py` - OSS 客户端

---

## 📁 目录结构详解

详细的目录结构说明请参考 [structure.md](./structure.md)。
