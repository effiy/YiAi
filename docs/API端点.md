# API 端点文档

本文档详细介绍 YiAi 项目的所有 API 端点。

---

## ⚡ 执行模块

YiAi 的核心扩展机制，允许通过 REST API 动态执行 Python 模块方法。

### 主要特性

#### 灵活的执行方式
- **GET 请求**：通过 URL 参数执行模块方法
- **POST 请求**：通过 JSON 请求体执行模块方法
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

### API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/execution` | 通过 GET 请求执行模块方法 |
| POST | `/execution` | 通过 POST 请求执行模块方法 |

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

## 📤 文件上传与管理

提供文件上传、读取、写入、删除和重命名等完整的文件管理功能。

### 主要特性

#### 双重存储支持
- **AliCloud OSS**：主存储方案，提供高可用的云存储
- **本地静态存储**：备用方案，当 OSS 未配置时自动 fallback
- **智能切换**：自动检测配置并选择合适的存储方式

#### 文件管理功能
- **多类型支持**：支持图片（jpg, jpeg, png, gif, webp, svg, bmp, ico）、文档（pdf, doc, docx, epub, md）等多种文件类型
- **Base64 上传**：支持 Base64 编码的图片直接上传
- **图片智能处理**：读取图片文件时返回静态 URL 而非 base64 编码
- **文件操作**：完整的 CRUD 操作（读取、写入、删除、重命名）
- **目录管理**：支持文件夹的删除和重命名

#### 安全控制
- **文件类型限制**：通过白名单控制允许的文件类型
- **大小限制**：可配置的最大文件大小限制
- **路径安全**：防止路径遍历攻击的安全验证

### API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/upload` | 通用文件上传（JSON 方式） |
| POST | `/upload-image-to-oss` | 图片上传到 OSS（支持本地存储 fallback） |
| POST | `/upload/upload-image-to-oss` | 图片上传到 OSS（别名） |
| POST | `/read-file` | 读取文件内容 |
| POST | `/write-file` | 写入文件 |
| POST | `/delete-file` | 删除文件 |
| POST | `/delete-folder` | 删除文件夹 |
| POST | `/rename-file` | 重命名文件 |
| POST | `/rename-folder` | 重命名文件夹 |

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

## 🏢 企业微信

企业微信机器人 Webhook 集成功能，支持向企业微信群发送消息。

### 主要特性
- **Webhook 集成**：通过企业微信机器人 Webhook 发送消息
- **格式验证**：自动验证 Webhook URL 格式
- **错误处理**：完善的错误处理和日志记录
- **超时控制**：请求超时保护

### API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/wework/send-message` | 发送消息到企业微信机器人 |

### API 调用示例

```bash
POST /wework/send-message
{
  "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
  "content": "Hello from YiAi!"
}
```

### 相关文件
- `src/api/routes/wework.py` - 企业微信 API 端点

---

## 🔧 维护工具

系统维护和清理工具，帮助保持系统整洁。

### 主要特性
- **扫描静态图片**：扫描 static 目录下的所有图片文件
- **检测引用关系**：检查数据库 sessions 集合中引用的图片
- **识别未使用图片**：找出未被引用的图片文件
- **清理会话数据**：可选地清理引用了不存在图片的 sessions
- **Dry-run 模式**：支持预览删除结果，避免误操作
- **空间统计**：计算可释放的存储空间

### API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/cleanup-unused-images` | 清理未引用的图片 |
| POST | `/maintenance/cleanup-unused-images` | 清理未引用的图片（别名） |

### API 调用示例

```bash
POST /cleanup-unused-images
{
  "dry_run": true,
  "cleanup_sessions": false
}
```

### 相关文件
- `src/api/routes/maintenance.py` - 维护工具 API 端点
