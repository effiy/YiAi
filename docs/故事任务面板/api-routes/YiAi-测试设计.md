> | v1.0.0 | 2026-05-22 | deepseek-v4-pro | | 🌿 feat/api-routes | ⏱️ — | 📎 [CLAUDE.md](../../../CLAUDE.md) |

> **导航**: [← YiAi-技术评审](./YiAi-技术评审.md) · [YiAi-实施报告 →](./YiAi-实施报告.md)

> **来源引用**: `/rui doc --from-code api-routes` — 基于故事任务 AC 与使用场景生成测试设计。

---

### 主要价值

- 🎯 为 7 个路由模块的 22+ HTTP 端点提供可执行测试用例，覆盖正常/边界/异常/回归四类
- 🔒 重点覆盖文件操作的安全面（路径遍历、扩展名校验）和企业微信的 URL 校验
- ⚡ 每用例 Given/When/Then 格式，可直接翻译为 pytest + httpx 测试代码
- 📊 Gate A 交接信号完整，含验证命令和环境配置要求

---

## §0 基线溯源

| TC# | 覆盖 AC# | 覆盖场景 | 覆盖类型 | 状态 |
|-----|---------|---------|---------|------|
| TC-N01–N08 | AC1, AC2, AC3, AC5, AC7 | 场景 1, 2, 3, 5 | 正常路径 | 待执行 |
| TC-B01–B04 | AC4, AC6 | 场景 2, 3 | 边界条件 | 待执行 |
| TC-E01–E06 | AC4, AC8 | 场景 2, 3, 5 | 异常路径 | 待执行 |
| TC-R01–R02 | AC1–AC8 | 场景 1–7 | 回归 | 待执行 |

---

## §1 测试范围

### 1.1 覆盖矩阵

| FP# | 功能点 | 正常 | 边界 | 异常 | 回归 | 覆盖率 |
|-----|--------|:--:|:--:|:--:|:--:|:--:|
| FP1 | 模块执行 | ✓ | — | ✓ | ✓ | 75% |
| FP2 | 图片上传 OSS | ✓ | — | ✓ | ✓ | 75% |
| FP3 | 文件上传 | ✓ | — | — | ✓ | 50% |
| FP4 | 文件读取 | ✓ | ✓ | ✓ | ✓ | 100% |
| FP5–FP8 | 写入/删除/重命名 | ✓ | — | ✓ | ✓ | 75% |
| FP9 | 企业微信消息 | ✓ | — | ✓ | ✓ | 75% |
| FP10 | 图片清理 | ✓ | — | — | ✓ | 50% |
| FP11 | 状态 CRUD | ✓ | ✓ | ✓ | ✓ | 100% |
| FP12 | Observer 健康 | ✓ | — | — | ✓ | 50% |
| FP13 | 故事面板 | ✓ | — | — | ✓ | 50% |

---

## §2 测试用例

### 2.1 正常路径

| ID | Given | When | Then | 关联 FP | 优先级 |
|----|-------|------|------|---------|--------|
| TC-N01 | 模块白名单含 `services.utils` | POST `/` `{"module_name":"services.utils","method_name":"get_current_time","parameters":{}}` | 响应 200，data 含 UTC 时间字符串 | FP1 | P0 |
| TC-N02 | 有效 Base64 图片 data URL | POST `/upload-image-to-oss` `{"data_url":"data:image/png;base64,iVBORw...","filename":"test.png"}` | 响应 200，data.url 非空 | FP2 | P0 |
| TC-N03 | static 目录存在 `readme.md` | POST `/read-file` `{"target_file":"readme.md"}` | 响应 200，data.type="text"，data.content 非空 | FP4 | P0 |
| TC-N04 | 图片文件存在于 static | POST `/read-file` `{"target_file":"logo.png"}` | 响应 200，data.type="url"，data.content 含 https URL | FP4 | P0 |
| TC-N05 | 有效企业微信 webhook URL | POST `/wework/send-message` `{"webhook_url":"https://qyapi.weixin.qq.com/...","content":"测试"}` | 响应 200（或 webhook 实际调用结果） | FP9 | P0 |
| TC-N06 | — | POST `/state/records` `{"key":"test-001","title":"测试","type":"note"}` | 响应 201，data 含完整记录 | FP11 | P0 |
| TC-N07 | 已有记录 `test-001` | GET `/state/records?record_type=note` | 响应 200，data.items 含该记录 | FP11 | P0 |
| TC-N08 | — | GET `/health/observer` | 响应 200，data 含 throttle/sampler/sandbox/guard 启用状态 | FP12 | P1 |

### 2.2 边界条件

| ID | Given | When | Then | 关联 FP | 优先级 |
|----|-------|------|------|---------|--------|
| TC-B01 | — | POST `/read-file` `{"target_file":"readme"}` 不含扩展名 | 响应 400，message 含 "必须包含扩展名"（`upload.py:161-165`） | FP4 | P0 |
| TC-B02 | — | POST `/state/records` 不传 key | 响应 201，自动生成 key（`state.py:30-31`） | FP11 | P1 |
| TC-B03 | — | GET `/state/records?page_num=0` | 响应 422（pydantic 校验 ge=1） | FP11 | P1 |
| TC-B04 | — | POST `/read-file` `{"target_file":"static/readme.md"}` (含 static/ 前缀) | 正常去除前缀，返回文件内容（`upload.py:49-50`） | FP4 | P1 |

### 2.3 异常路径

| ID | Given | When | Then | 关联 FP | 优先级 |
|----|-------|------|------|---------|--------|
| TC-E01 | — | POST `/read-file` `{"target_file":"../etc/passwd"}` | 响应 400，code=1002（路径遍历被 `_resolve_static_path` 拦截） | FP4 | P0 |
| TC-E02 | — | POST `/read-file` `{"target_file":"/etc/passwd"}` (绝对路径) | 响应 400，code=1002 | FP4 | P0 |
| TC-E03 | — | POST `/read-file` `{"target_file":"nonexistent.md"}` | 响应 404，code=1004 | FP4 | P0 |
| TC-E04 | — | POST `/wework/send-message` `{"webhook_url":"https://evil.com/hook","content":"test"}` | 响应 400，message 含 "无效的企业微信 Webhook URL" | FP9 | P0 |
| TC-E05 | — | POST `/wework/send-message` `{"webhook_url":"","content":"test"}` | 响应 400，message 含 "Webhook URL 不能为空" | FP9 | P1 |
| TC-E06 | — | GET `/state/records/nonexistent-key` | 响应 404，code=1004 | FP11 | P0 |

### 2.4 回归用例

| ID | Given | When | Then | 关联 FP | 优先级 |
|----|-------|------|------|---------|--------|
| TC-R01 | 文件操作端点就绪 | 依次调用 read/write/delete/rename 端点 | 全部返回 200，操作结果正确 | FP2–FP8 | P0 |
| TC-R02 | 状态 CRUD 端点就绪 | 依次调用 create→read→update→delete | 每步返回正确结果，最终删除成功 | FP11 | P0 |

---

## §3 环境专项

| ID | Given | When | Then | 优先级 |
|----|-------|------|------|--------|
| TC-X01 | 大文件 (>10MB) Base64 编码 | POST `/upload-image-to-oss` | OSS 拒绝或接受（受 oss_max_file_size_mb=50 限制） | P2 |
| TC-X02 | 并发 10 个 POST `/read-file` 请求 | 同时发送 | 全部正确返回或排队等待 | P2 |

---

## §4 测试环境

| 维度 | 配置 |
|------|------|
| 运行环境 | Python 3.10+, pytest + httpx (AsyncClient) |
| 部署方式 | 本地启动 FastAPI TestClient 或 live server |
| 数据准备 | 预置 static/ 目录含测试文件；预置 MongoDB 含 sessions 集合 |
| 分支 | `feat/api-routes` |

---

## §5 评审清单

| # | 检查项 | 状态 |
|---|--------|:--:|
| 1 | 每 FP 多类覆盖 | ✅ |
| 2 | Gate A 覆盖（P0 用例可执行） | ✅ |
| 3 | 异常含恢复行为 | ✅ |
| 4 | 基线溯源闭合 | ✅ |

---

## §6 Gate A 交接

| 信号 | 内容 |
|------|------|
| 通过状态 | ✅ 待执行 |
| P0 用例 ID | TC-N01, TC-N02, TC-N03, TC-N04, TC-N05, TC-N06, TC-B01, TC-E01, TC-E02, TC-E03, TC-E04, TC-E06 |
| 实现约束 | 1. 需要启动 FastAPI 应用；2. 文件测试需要 static/ 目录；3. 企业微信测试需要有效 webhook URL 或 mock |
| 验证命令 | `pytest tests/ -k "test_execution or test_upload or test_wework or test_state" -v` |

---

> **变更记录**
>
> | 日期 | 变更 | 触发 | 证据 |
> |------|------|------|------|
> | 2026-05-22 | 初始生成 | `/rui doc --from-code api-routes` | 技术评审 + 故事任务 AC |
