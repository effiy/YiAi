# 核心功能介绍

本文档详细介绍 YiAi 项目的核心功能。

## 🤖 AI 聊天服务

YiAi 集成了 Ollama 本地 AI 模型，提供强大的对话能力。

### 主要特性
- **本地 AI 模型**：基于 Ollama，无需依赖外部云服务
- **多轮对话**：支持上下文理解的连续对话
- **历史记录**：聊天历史自动存储到 MongoDB
- **模型切换**：可通过配置灵活切换不同的 AI 模型
- **异步处理**：高效的异步请求处理

### 相关文件
- `src/services/ai/ollama_client.py` - Ollama 客户端实现

---

## 📰 RSS 源管理

提供自动化的 RSS 源内容抓取和管理功能。

### 主要特性
- **定时抓取**：可配置的自动抓取调度器
- **灵活间隔**：支持自定义抓取间隔（秒）
- **多源管理**：同时管理多个 RSS 源
- **数据持久化**：文章内容存储到 MongoDB 数据库
- **生命周期管理**：应用启动时自动启动调度器，关闭时优雅停止

### 配置项
- `rss.scheduler_enabled` - 是否启用 RSS 调度器
- `rss.scheduler_interval` - 抓取间隔（秒）

### 相关文件
- `src/services/rss/scheduler.py` - RSS 调度器
- `src/services/rss/parser.py` - RSS 解析器

---

## 📤 文件上传与存储

提供灵活的文件上传和存储解决方案，支持云存储和本地存储两种模式。

### 主要特性

#### 双重存储支持
- **AliCloud OSS**：主存储方案，提供高可用的云存储
- **本地静态存储**：备用方案，当 OSS 未配置时自动 fallback
- **智能切换**：自动检测配置并选择合适的存储方式

#### 文件管理功能
- **多类型支持**：支持图片（jpg, jpeg, png, gif, webp, svg, bmp, ico）、文档（pdf, doc, docx, epub, md）等多种文件类型
- **标签系统**：支持为文件添加标签，便于分类和检索
- **元数据存储**：文件信息（标题、描述等）存储到数据库
- **Base64 上传**：支持 Base64 编码的图片直接上传
- **文件操作**：完整的 CRUD 操作（读取、写入、删除、重命名）
- **目录管理**：支持文件夹的创建、删除和重命名

#### 安全控制
- **文件类型限制**：通过白名单控制允许的文件类型
- **大小限制**：可配置的最大文件大小限制
- **路径安全**：防止路径遍历攻击的安全验证

### 配置项
- `oss.access_key` - OSS 访问密钥
- `oss.secret_key` - OSS 秘密密钥
- `oss.endpoint` - OSS 接入点
- `oss.bucket` - OSS 存储空间名称
- `oss.max_file_size_mb` - 最大文件大小（MB）
- `oss.allowed_extensions` - 允许的文件扩展名列表
- `static.base_dir` - 本地静态文件存储目录
- `static.base_url` - 静态文件访问 URL 前缀

### 相关文件
- `src/services/storage/oss_client.py` - OSS 存储客户端
- `src/api/routes/upload.py` - 文件上传 API 端点

---

## ⚡ 动态模块执行引擎

YiAi 的核心扩展机制，允许通过 REST API 动态执行 Python 模块方法。

### 主要特性

#### 灵活的执行方式
- **同步函数**：支持普通同步函数执行
- **异步函数**：原生支持 async/await 异步函数
- **生成器**：支持返回迭代器的生成器函数
- **异步生成器**：支持异步生成器函数
- **SSE 流式传输**：为生成器提供 Server-Sent Events 流式响应

#### 安全控制
- **白名单机制**：通过 `config.yaml` 中的 `module.allowlist` 控制允许执行的模块
- **灵活配置**：使用 `["*"]` 表示允许所有模块，或指定具体模块路径

#### 参数处理
- **字典参数**：直接传递字典作为参数
- **JSON 字符串**：支持 JSON 格式的字符串参数
- **自动解析**：自动检测并解析参数格式

### 使用示例

```python
await execute_module(
    module_path="services.storage.oss_client",
    function_name="list_files",
    parameters={"directory": "images/"}
)
```

### API 调用示例

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

### 配置项
- `module.allowlist` - 允许执行的模块白名单

### 相关文件
- `src/services/execution/executor.py` - 模块执行引擎
- `src/api/routes/execution.py` - 执行 API 端点

---

## 🛡️ 安全与认证

提供完善的安全保护和认证机制。

### 主要特性

#### 认证中间件
- **令牌认证**：支持基于令牌的 API 认证
- **灵活配置**：可通过配置启用或禁用认证
- **开发友好**：开发环境可方便地关闭认证

#### 异常处理
- **统一异常处理**：全局异常捕获和处理机制
- **标准化响应**：统一的错误响应格式
- **错误码系统**：完善的错误码定义
- **业务异常**：自定义业务异常类型

#### 日志系统
- **结构化日志**：统一的日志格式
- **多级别支持**：DEBUG、INFO、WARNING、ERROR 等日志级别
- **可配置级别**：通过配置文件调整日志级别

### 配置项
- `middleware.auth_enabled` - 是否启用认证
- `middleware.auth_token` - 认证令牌
- `logging.level` - 日志级别
- `logging.format` - 日志格式

### 相关文件
- `src/core/middleware.py` - 认证中间件
- `src/core/exceptions.py` - 自定义异常
- `src/core/error_codes.py` - 错误码定义
- `src/core/exception_handler.py` - 全局异常处理器
- `src/core/logger.py` - 日志配置
