# Network 文档

> 网络请求约定与 API 通信规范

---

## 请求库

- **服务端 HTTP 客户端**：`aiohttp`（异步）
- **服务端 HTTP 框架**：`FastAPI` + `Uvicorn`
- **外部调用示例**：企业微信 Webhook (`services/ai/chat_service.py` 中的 Ollama 调用)

## 封装入口

| 入口 | 文件 | 用途 |
|------|------|------|
| FastAPI 应用 | `src/main.py` | HTTP 服务端入口 |
| aiohttp 客户端 | `src/api/routes/wework.py` | 企业微信 Webhook 发送 |
| Ollama 客户端 | `src/services/ai/chat_service.py` | AI 聊天服务调用 |

## BaseURL

- **开发环境**：`http://0.0.0.0:8000`
- **生产环境**：`https://api.effiy.cn`
- **静态文件**：`https://api.effiy.cn/static`

## Header / 认证

### CORS 配置

默认允许所有来源：
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
Access-Control-Allow-Headers: *
```

### 认证中间件

当 `middleware.auth_enabled` 为 `true` 时，需携带请求头：
```
X-Token: <your-token>
```

白名单路径（无需认证）：
- `/write-file`
- `/read-file`
- `/delete-file`
- `/upload`
- `/static/*`
- `/mcp*`

## 错误处理

### 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 错误码分组

| 分组 | 范围 | 说明 |
|------|------|------|
| 成功 | 0 | 业务成功 |
| 客户端错误 | 1xxx | 参数错误、未认证、权限不足等 |
| 服务端错误 | 5xxx | 内部错误、数据库操作失败等 |

### 常见错误码

| 错误码 | HTTP 状态 | 说明 |
|--------|----------|------|
| 0 | 200 | 成功 |
| 1000 | 400 | 无效请求 |
| 1002 | 400 | 无效参数 |
| 1004 | 404 | 未找到资源 |
| 1009 | 401 | 未认证 |
| 1008 | 403 | 权限拒绝 |
| 5000 | 500 | 服务器繁忙 |
| 5001 | 500 | 内部错误 |

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 401 未授权 | 未携带 X-Token 或令牌错误 | 检查请求头或临时禁用认证 |
| CORS 错误 | 预检请求未通过 | 确认 Origin 在允许列表中（默认允许所有） |
| 422 验证错误 | 请求参数不符合 Pydantic 模型 | 检查参数类型和必填项 |
| 500 内部错误 | 业务逻辑异常或未捕获错误 | 查看服务端日志定位问题 |
