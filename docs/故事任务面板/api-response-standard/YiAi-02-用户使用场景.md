# YiAi-02-用户使用场景

## 场景 1：客户端统一解析 API 响应

**角色**：前端开发者 / 第三方 API 消费者

**前置条件**：客户端已配置 API Base URL 和 X-Token

**操作流程**：
1. 客户端调用任意 API 端点（如 `POST /upload/read-file`）
2. 解析响应 JSON，读取顶层 `code` 字段
3. 若 `code === 0`，从 `data` 字段获取业务数据
4. 若 `code !== 0`，读取 `message` 字段展示错误提示

**期望结果**：
- 所有端点返回格式一致：`{"code": int, "message": str, "data": any}`
- 例外：SSE 流式端点（`execution.py` 的流式接口）可豁免信封格式

**当前问题**：`/health/observer` 返回 `{"throttle_enabled": false, ...}`，不包含 `code`/`message`/`data` 字段，客户端需特殊处理。

---

## 场景 2：错误码驱动的客户端行为

**角色**：前端开发者

**前置条件**：客户端已实现错误码映射表

**操作流程**：
1. 客户端请求 `GET /state/records/nonexistent-key`
2. 收到响应 `{"code": 1004, "message": "未找到资源", "data": null}`
3. 根据 `code === 1004` 展示「资源不存在」提示，不触发全局异常弹窗
4. 客户端请求时网络超时，收到 `{"code": 5000, "message": "服务器繁忙", "data": null}`
5. 根据 `code === 5000` 展示「服务器繁忙，请稍后重试」提示

**期望结果**：
- 客户端可根据 `code` 精确区分错误类型（参数错误 vs 资源不存在 vs 服务端错误）
- 同一语义永远映射到同一业务码

**当前问题**：
- `INVALID_PARAMS`(1002) 同时用于「参数格式错误」和「资源不存在」，客户端无法区分
- `DATA_STORE_FAIL`(1005) 业务码是 1xxx 但语义是服务端错误，客户端错误处理逻辑混乱

---

## 场景 3：健康检查监控

**角色**：运维人员 / 监控系统

**前置条件**：Prometheus/Grafana 或自定义监控脚本已配置

**操作流程**：
1. 监控系统定期请求 `GET /health/observer`
2. 解析 `code` 判断服务是否正常
3. 从 `data` 字段获取 Observer 组件状态详情

**期望结果**：
- 健康检查端点与业务端点使用相同的响应信封
- 监控脚本无需为健康检查端点编写特殊解析逻辑

---

## 场景 4：文件删除幂等性语义

**角色**：前端开发者 / 自动化脚本

**前置条件**：用户触发文件删除操作

**操作流程**：
1. 客户端请求 `POST /upload/delete-file`，传入 `target_file: "temp/old-data.json"`
2. 若文件存在，删除成功返回 `{"code": 0, "message": "success", "data": {"message": "删除成功"}}`
3. 若文件不存在，返回 `{"code": 1004, "message": "文件不存在: temp/old-data.json", "data": null}`

**期望结果**：
- 客户端可区分「删除成功」与「文件本就不存在」
- 删除不存在文件不静默返回成功

**当前问题**：删除不存在文件返回 `code: 0`，调用方以为操作成功。

---

## 场景 5：POST 创建资源的 HTTP 语义

**角色**：RESTful API 消费者

**前置条件**：客户端遵循 HTTP 标准

**操作流程**：
1. 客户端请求 `POST /state/records` 创建新记录
2. 检查 HTTP 状态码是否为 201（Created）
3. 从响应体 `data` 字段获取新建记录详情

**期望结果**：
- 创建成功返回 HTTP 201，响应体仍包含 `{code: 0, message: "success", data: {...}}`
- 创建失败返回对应的错误 HTTP 状态码（400/500）

**当前问题**：路由声明 `status_code=201`，但 `success()` 内部硬编码 200，实际返回 200。
