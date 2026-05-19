# YiAi-01-故事任务

## 故事标识

- **名称**：api-response-standard
- **标题**：统一 API 响应数据结构与错误码规范
- **类型**：backend（后端重构）
- **优先级**：P0（影响所有 API 消费者的契约一致性）

## 问题陈述

当前项目存在 6 类 API 响应规范不一致问题，导致客户端需要特殊处理不同接口的返回格式：

1. **错误码范围错位**：`DATA_STORE_FAIL`(1005)、`DATA_UPDATE_FAIL`(1006)、`DATA_DESTROY_FAIL`(1007) 的业务码属于 1xxx（客户端错误）范围，但语义上是服务端错误（HTTP 500），与文件头注释的分类矛盾
2. **响应信封逃逸**：`/health/observer` 返回裸 `ObserverHealth` Pydantic 模型，不经过 `{code, message, data}` 信封
3. **HTTP 状态码虚假声明**：`POST /state/records` 装饰器声明 `status_code=201`，但 `success()` 内部硬编码返回 200
4. **错误码语义滥用**：`INVALID_PARAMS` 被用于「资源不存在」场景（应使用 `DATA_NOT_FOUND`）；`INTERNAL_ERROR` 被过度使用于写/重命名操作（应使用专门的 `DATA_STORE_FAIL`/`DATA_UPDATE_FAIL`）
5. **删除操作静默成功**：`delete_file`/`delete_folder` 对不存在的资源返回 `success()`，调用方无法区分「已删除」与「本来就不存在」
6. **错误机制不统一**：`story_panel.py` 混用 `fail()` 和 `raise HTTPException`，增加认知负担

## 解决方案

1. 重编号 `DATA_STORE_FAIL`/`DATA_UPDATE_FAIL`/`DATA_DESTROY_FAIL` 到 5xxx 范围（5002/5003/5004）
2. `observer_health.py` 改用 `success()` 包装返回值
3. `state.py` 的 `create_record` 移除无效的 `status_code=201`，或改造 `success()` 支持自定义 HTTP 状态码
4. 全量审计所有路由的错误码使用，修正语义错配
5. 删除不存在资源改为返回错误（`DATA_NOT_FOUND`）
6. `story_panel.py` 中的 `HTTPException` 替换为 `BusinessException`

## 影响范围

| 文件 | 变更类型 |
|------|---------|
| `src/core/error_codes.py` | 重编号 + 新增错误码 |
| `src/core/response.py` | `success()` 支持自定义 HTTP 状态码 |
| `src/api/routes/observer_health.py` | 响应信封修正 |
| `src/api/routes/state.py` | HTTP 状态码修正 |
| `src/api/routes/upload.py` | 错误码审计 + 删除语义修正 |
| `src/api/routes/story_panel.py` | 错误机制统一 |
| `src/api/routes/wework.py` | 错误码审计（确认 `INTERNAL_ERROR` 使用合理性） |
| `src/api/routes/maintenance.py` | 错误码审计 |
| `src/api/routes/execution.py` | 错误码审计 |

## 验收标准

- [ ] `ErrorCode` 枚举中所有 5xx 语义的错误码均在 5xxx 范围
- [ ] 所有 API 端点（含 `/health/observer`）返回统一的 `{code, message, data}` 信封
- [ ] `POST /state/records` 创建成功时返回 HTTP 201
- [ ] 不存在资源请求返回 `DATA_NOT_FOUND`(1004)，不返回 `INVALID_PARAMS`(1002)
- [ ] 删除不存在资源返回错误响应，不返回 `code: 0`
- [ ] 所有路由仅使用 `BusinessException` 抛出业务错误，不使用裸 `HTTPException`
- [ ] 无现有功能测试回归
