# Dynamic Execution API — 参考手册

> | v1.0 | 2026-05-13 | deepseek-v4-pro | 🌿 feat/YiAi-doc-from-code |

## 端点总览

| 方法 | 路径 | operation_id | 描述 |
|------|------|-------------|------|
| GET | `/` | `execute_module_get` | 通过查询参数执行模块函数 |
| POST | `/` | `execute_module_post` | 通过 JSON Body 执行模块函数 |

---

## GET / — execute_module_get

### 请求

**查询参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `module_name` | string | 否 | `""` | 目标模块全路径，如 `services.ai.chat_service` |
| `method_name` | string | 否 | `""` | 目标函数名，如 `chat` |
| `parameters` | string (JSON) | 否 | `{}` | JSON 字符串，传递给目标函数的参数字典 |

**请求示例**：

```
GET /?module_name=services.ai.chat_service&method_name=list_ollama_models&parameters=%7B%7D
```

解码后 parameters = `{}`

### 响应

**非流式（普通返回值）**：

```json
{
  "code": 0,
  "data": { /* 目标函数的返回值 */ }
}
```

**流式（async generator / generator）**：

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"data":{"message":"..."}}

data: {"done":true}
```

### 错误

| HTTP 状态码 | code | 触发条件 |
|-------------|------|---------|
| 200 | 1002 | `module_name` 或 `method_name` 为空 |
| 200 | 1003 | 模块不在白名单内 |
| 200 | 1002 | 模块导入失败、函数不存在、参数 JSON 非法 |
| 200 | 1004 | 重入深度超限 |
| 200 | 1001 | 目标函数执行时内部异常 |

> 响应统一通过 `success()`/`fail()` 包装，HTTP 状态码保持 200，错误信息在 `code` + `message` 字段中。

---

## POST / — execute_module_post

### 请求

**请求体**（`ExecuteRequest`）：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `module_name` | string | 否 | `""` | 目标模块全路径 |
| `method_name` | string | 否 | `""` | 目标函数名 |
| `parameters` | dict \| string | 否 | `{}` | 参数字典或 JSON 字符串 |

**请求示例**：

```json
{
  "module_name": "services.ai.chat_service",
  "method_name": "chat",
  "parameters": {
    "user": "Hello, how are you?",
    "model": "qwen3.5"
  }
}
```

### 响应

同 GET 端点。流式响应自动检测：async generator / generator 返回 SSE 流，普通值返回 JSON。

### 错误

同 GET 端点，额外：

| 触发条件 | code |
|---------|------|
| 请求体 JSON 格式错误 | FastAPI 自动返回 422 |

---

## 支持的目标函数签名

| 签名类型 | 检测方式 | 响应格式 |
|---------|---------|---------|
| `async def fn(params: dict) -> Any` | `iscoroutinefunction` | JSON (`success(data=result)`) |
| `def fn(params: dict) -> Any` | 同步普通函数 | JSON |
| `async def fn(params: dict) -> AsyncIterator` | `isasyncgenfunction` | SSE 流 |
| `def fn(params: dict) -> Iterator` | `isgeneratorfunction` | SSE 流 |

**约定**：所有目标函数接收单一的 `params: dict` 参数。

---

## 当前白名单内的可调用模块

> 白名单由 `config.yaml` 的 `module_allowlist` 控制，默认 `["*"]` 表示全部放行。

| module_name | method_name | 功能 |
|-------------|------------|------|
| `services.ai.chat_service` | `chat` | Ollama AI 对话（流式/非流式） |
| `services.ai.chat_service` | `list_ollama_models` | 获取可用模型列表 |
| `services.rss.rss_scheduler` | `parse_all_enabled_rss_sources` | 批量解析 RSS |
| `services.rss.rss_scheduler` | `start_rss_scheduler` | 启动 RSS 调度器 |
| `services.rss.rss_scheduler` | `stop_rss_scheduler` | 停止 RSS 调度器 |
| `services.rss.rss_scheduler` | `set_scheduler_config` | 设置调度器配置 |
| `services.rss.rss_scheduler` | `get_scheduler_status_info` | 获取调度器状态 |

---

```
← [00-索引](./00-索引.md) · ↑ [接口文档索引](../) · → [02-接口架构蓝图](./02-接口架构蓝图.md)
```
