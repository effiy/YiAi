# YiAi-05-测试用例评审

## 测试策略

本故事为纯后端重构，不涉及新功能。测试以**回归验证**为主，确保所有现有 API 行为不受影响（或按预期变更）。

## 测试用例

### TC1: 响应信封一致性

| 项目 | 内容 |
|------|------|
| **端点** | `GET /health/observer` |
| **输入** | 无 |
| **预期** | 返回 `{"code": 0, "message": "success", "data": {...}}` |
| **验证点** | 顶层包含 `code`/`message`/`data` 三个字段；`data` 内包含原 `ObserverHealth` 全部字段 |

### TC2: 创建资源返回 HTTP 201

| 项目 | 内容 |
|------|------|
| **端点** | `POST /state/records` |
| **输入** | `{"record_type": "test", "title": "test", "payload": {}}` |
| **预期** | HTTP 状态码 201，响应体 `code: 0` |
| **验证点** | `response.status_code == 201` |

### TC3: 查询成功返回 HTTP 200

| 项目 | 内容 |
|------|------|
| **端点** | `GET /state/records` |
| **输入** | 无 |
| **预期** | HTTP 200，`code: 0`，`data` 包含查询结果 |

### TC4: 查询不存在资源返回 404

| 项目 | 内容 |
|------|------|
| **端点** | `GET /state/records/nonexistent-key-12345` |
| **输入** | 不存在的 key |
| **预期** | HTTP 404，`code: 1004`，`message` 包含 "not found" |

### TC5: 读取不存在文件返回 404

| 项目 | 内容 |
|------|------|
| **端点** | `POST /upload/read-file` |
| **输入** | `{"target_file": "nonexistent/file.txt"}` |
| **预期** | HTTP 404，`code: 1004` |
| **验证点** | 不再返回 `code: 1002`（INVALID_PARAMS） |

### TC6: 删除不存在文件返回错误

| 项目 | 内容 |
|------|------|
| **端点** | `POST /upload/delete-file` |
| **输入** | `{"target_file": "nonexistent/file.txt"}` |
| **预期** | HTTP 404，`code: 1004` |
| **验证点** | `code !== 0`（不再静默返回成功） |

### TC7: 删除不存在目录返回错误

| 项目 | 内容 |
|------|------|
| **端点** | `POST /upload/delete-folder` |
| **输入** | `{"target_dir": "nonexistent_dir"}` |
| **预期** | HTTP 404，`code: 1004` |

### TC8: 参数校验失败返回 400

| 项目 | 内容 |
|------|------|
| **端点** | `POST /upload/read-file` |
| **输入** | `{"target_file": ""}` (空字符串) |
| **预期** | HTTP 400，`code: 1002` |

### TC9: 数据存储错误码校验

| 项目 | 内容 |
|------|------|
| **端点** | `POST /upload/write-file` (模拟磁盘满/权限不足) |
| **输入** | 正常文件写入请求 |
| **预期** | HTTP 500，`code: 5002` (DATA_STORE_FAIL) |

### TC10: 数据更新错误码校验

| 项目 | 内容 |
|------|------|
| **端点** | `POST /upload/rename-file` (模拟 I/O 失败) |
| **输入** | 正常重命名请求 |
| **预期** | HTTP 500，`code: 5003` (DATA_UPDATE_FAIL) |

### TC11: 数据删除错误码校验

| 项目 | 内容 |
|------|------|
| **端点** | `POST /upload/delete-file` (模拟文件被锁定) |
| **输入** | 存在的文件 |
| **预期** | HTTP 500，`code: 5004` (DATA_DESTROY_FAIL) |

### TC12: story_panel 参数校验错误机制统一

| 项目 | 内容 |
|------|------|
| **端点** | `GET /api/story-panel/stories/Invalid Name` |
| **输入** | 含空格的 name |
| **预期** | HTTP 400，`code: 1002`，通过 `BusinessException` 而非裸 `HTTPException` 抛出 |
| **验证点** | 响应体仍为标准 `{code, message, data}` 格式 |

### TC13: 未认证请求

| 项目 | 内容 |
|------|------|
| **端点** | 任意需要认证的端点（无 X-Token） |
| **输入** | 无认证头 |
| **预期** | HTTP 401，`code: 1009` |

## 测试环境

- 本地开发环境（无需 MongoDB 连接即可运行参数校验类测试）
- 需要 MongoDB 的端到端测试使用 `pytest-asyncio` + `httpx.AsyncClient`

## 门禁标准

- 所有 TC1-TC13 通过方可进入实现阶段
- 无回归：所有已有路由的成功路径不受影响
