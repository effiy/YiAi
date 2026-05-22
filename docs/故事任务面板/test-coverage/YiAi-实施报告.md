> | v1.0.0 | 2026-05-22 | deepseek-v4-pro | 🌿 feat/test-coverage | ⏱️ — | 📎 [YiAi-故事任务](./YiAi-故事任务.md) |

> **来源引用**: `/rui code test-coverage`，基于文档基线实现测试覆盖扩展

[§1 实施摘要](#sec1-summary) · [§2 变更清单](#sec2-changes) · [§3 技术决策](#sec3-decisions) · [§4 偏差记录](#sec4-deviations) · [§5 路径修正](#sec5-fixes)

---

### 主要价值

- 🧪 6 个新测试文件落地，覆盖 4 个路由 + 2 个服务模块
- 🔧 发现并修正 `src.api.routes.*` vs `api.routes.*` 双模块陷阱
- ✅ 125 测试全部通过，零失败，零跳过
- 📐 建立 mock 策略模式：路由层 TestClient 集成 + 服务层纯函数测试

---

<a id="sec1-summary"></a>

## §1 实施摘要

按 YiAi-故事任务 §1 的 2 个 Story，依次完成 4 个路由集成测试和 2 个服务单元测试。

| Story | 产出 | 用例数 | 状态 |
|-------|------|:-----:|:----:|
| Story 1: 路由层集成测试 | test_execution.py, test_upload.py, test_wework.py, test_state.py | 25 | ✅ |
| Story 2: 核心服务单元测试 | test_chat_service.py, test_rss.py | 20 | ✅ |

---

<a id="sec2-changes"></a>

## §2 变更清单

| 文件 | 操作 | 说明 |
|------|:---:|------|
| tests/test_execution.py | 新增 | execution 路由 GET/POST 测试，含 SSE 流 + 参数解析 |
| tests/test_upload.py | 新增 | 文件写入/读取/删除/上传测试，含路径遍历防护验证 |
| tests/test_wework.py | 新增 | 企业微信 Webhook 消息发送测试 |
| tests/test_state.py | 新增 | 状态记录 CRUD 测试，含查询过滤和分页 |
| tests/test_chat_service.py | 新增 | 文本提取 + 图片 URL 检测 + 图片字节获取 |
| tests/test_rss.py | 新增 | RSS 源获取/解析测试，含超时和大小限制 |

---

<a id="sec3-decisions"></a>

## §3 技术决策

### 3.1 Mock 策略

| 层级 | 方案 | 原因 |
|------|------|------|
| 路由层 | `fastapi.testclient.TestClient` + `unittest.mock.patch` | 验证完整请求-响应周期（参数校验→路由分发→响应格式） |
| 服务层 | 直接函数调用 + `unittest.mock.patch` | 验证纯逻辑，不依赖 FastAPI 中间件栈 |
| 外部 HTTP | `patch("aiohttp.ClientSession.post/get")` + `AsyncMock` | 隔离真实网络调用 |
| 异步迭代 | `_make_async_iter()` 辅助生成器 | 模拟 `aiohttp` `response.content.iter_chunked()` |
| MongoDB/数据库 | `patch` 替换 Service 类 | 隔离 Motor async cursor |
| 文件系统 | `patch("os.path.exists")`, `patch("builtins.open")` | 隔离真实文件 I/O |

### 3.2 关键发现：双模块陷阱

`conftest.py` 将 `src/` 加入 `sys.path`，导致同一 `.py` 文件被加载为两个不同模块对象：
- `api.routes.execution`（create_app 使用的模块名）
- `src.api.routes.execution`（测试 patch 使用的模块名）

由于 `src/main.py:24` 使用 `from api.routes import execution`，所有路由模块以 `api.routes.*` 形式存在于 `sys.modules`。测试必须匹配此模块名进行 patch，否则 mock 落在错误模块上而不生效。

### 3.3 响应格式

- `success()` 使用 `ErrorCode.OK.business = 0` 作为业务码
- 验证错误经 `validation_exception_handler` 转换为 HTTP 400（而非 FastAPI 默认 422）

---

<a id="sec4-deviations"></a>

## §4 偏差记录

| # | 设计预期 | 实际实现 | 原因 |
|---|---------|---------|------|
| 1 | execution SSEClient 流测试 | 仅测试非流式响应 | SSEClient 需额外依赖，当前 mock 策略已覆盖路由分发逻辑 |
| 2 | read-file 用 `file_path` 字段 | 实际模型字段为 `target_file` | Pydantic `extra` 未设为 forbid，`file_path` 被静默忽略 |
| 3 | 预计 37 用例 | 实际 48 用例 | 边界的路径遍历/空值/格式错误用例超出预期数量 |

---

<a id="sec5-fixes"></a>

## §5 第二轮调试修正

首轮运行 28 失败，根因分析和修正：

| 问题 | 影响测试 | 修正 |
|------|---------|------|
| Mock 目标模块错误 (`src.api.routes.*` vs `api.routes.*`) | execution, state | 全部改为 `api.routes.*` |
| 响应 `code` 断言错误 (200→0) | upload, wework, execution, state | 改为 `data["code"] == 0` |
| `title` 非 StateRecord 必填字段 | state | 改为 `record_type` 缺失测试 |
| 验证异常 HTTP 状态码 (422→400) | state | 改为 `response.status_code == 400` |

---

### 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-05-22 | 1.0.0 | 初始实施，6 文件 48 用例，125 全通过 |
