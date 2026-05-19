# YiAi-06-后端实施报告

## 变更摘要

| 文件 | 变更行数 | 变更类型 |
|------|---------|---------|
| `src/core/error_codes.py` | +4/-4 | 错误码重编号 |
| `src/core/response.py` | +5/-4 | `success()` 新增 `http_code` 参数 |
| `src/api/routes/observer_health.py` | +4/-2 | 响应信封修正 |
| `src/api/routes/state.py` | +2/-3 | HTTP 状态码修正 |
| `src/api/routes/upload.py` | +9/-9 | 错误码审计 + 删除语义修正 |
| `src/api/routes/story_panel.py` | +5/-2 | 错误机制统一 |

## 变更详述

### 1. 错误码重编号 (`error_codes.py`)

```python
# 变更前
DATA_STORE_FAIL   = ErrorInfo(1005, HTTP_500, ...)  # 1xxx 范围错位
DATA_UPDATE_FAIL  = ErrorInfo(1006, HTTP_500, ...)
DATA_DESTROY_FAIL = ErrorInfo(1007, HTTP_500, ...)

# 变更后
SERVER_ERROR      = ErrorInfo(5000, HTTP_500, ...)
INTERNAL_ERROR    = ErrorInfo(5001, HTTP_500, ...)
DATA_STORE_FAIL   = ErrorInfo(5002, HTTP_500, ...)  # 5xxx 范围一致
DATA_UPDATE_FAIL  = ErrorInfo(5003, HTTP_500, ...)
DATA_DESTROY_FAIL = ErrorInfo(5004, HTTP_500, ...)
```

同时按数值排序整理 Server errors 段（5000→5004）。

### 2. `success()` 支持自定义 HTTP 状态码 (`response.py`)

新增 `http_code` 参数（默认 200），`JSONResponse(status_code=http_code, ...)` 替代硬编码 `ErrorCode.OK.http`。

### 3. 响应信封修正 (`observer_health.py`)

- 导入 `success`
- `ObserverHealth(...)` 先构造再通过 `success(data=health.model_dump())` 包装
- 移除 `response_model=ObserverHealth`（实际返回信封结构）

### 4. HTTP 状态码修正 (`state.py`)

`create_record` 的 `status_code=201` 从装饰器移至 `success(data=result, http_code=201)`。

### 5. 错误码审计 (`upload.py`)

| 位置 | 变更 |
|------|------|
| `read_file` 文件不存在 | `INVALID_PARAMS` → `DATA_NOT_FOUND` |
| `read_file` 不是文件 | `INVALID_PARAMS` → `DATA_NOT_FOUND` |
| `write_file` I/O 失败 | `INTERNAL_ERROR` → `DATA_STORE_FAIL` |
| `upload_file` I/O 失败 | `INTERNAL_ERROR` → `DATA_STORE_FAIL` |
| `delete_file` 不存在 | `success()` → `BusinessException(DATA_NOT_FOUND)` |
| `delete_folder` 不存在 | `success()` → `BusinessException(DATA_NOT_FOUND)` |
| `rename_file` I/O 失败 | `INTERNAL_ERROR` → `DATA_UPDATE_FAIL` |
| `rename_folder` I/O 失败 | `INTERNAL_ERROR` → `DATA_UPDATE_FAIL` |
| `_safe_rename` 源不存在 | `INVALID_PARAMS` → `DATA_NOT_FOUND` |

### 6. 错误机制统一 (`story_panel.py`)

`_validate_name()` 中的两处 `raise HTTPException(status_code=..., detail=...)` 替换为 `raise BusinessException(ErrorCode.INVALID_PARAMS, message=...)`。

## 不变式验证

- [x] 所有 5xx 语义错误码均在 5xxx 范围
- [x] 所有 API 端点返回 `{code, message, data}` 信封
- [x] `POST /state/records` 创建成功返回 HTTP 201
- [x] 不存在资源返回 `DATA_NOT_FOUND`(1004)
- [x] 删除不存在资源返回错误
- [x] 所有路由仅使用 `BusinessException`
- [x] 80/80 已有测试通过
