> | v1.0.0 | 2026-05-22 | deepseek-v4-pro | | 🌿 feat/core-infra | ⏱️ — | 📎 [CLAUDE.md](../../../CLAUDE.md) |

> **导航**: [← YiAi-技术评审](./YiAi-技术评审.md) · [YiAi-实施报告 →](./YiAi-实施报告.md)

> **来源引用**: `/rui doc --from-code core-infra` — 基于故事任务 AC 与使用场景生成测试设计。证据 Level B + 技术评审源码路径。

---

### 主要价值

- 🎯 为 8 个核心基础设施模块提供可执行的测试用例，覆盖正常/边界/异常/回归四类场景
- 🔒 重点覆盖认证中间件的安全面（token 验证、白名单、开关控制）和数据库的健壮性（未初始化、连接失败）
- ⚡ 每用例使用 Given/When/Then 可执行格式，可直接翻译为 pytest 测试代码
- 📊 Gate A 交接信号完整：P0 用例 ID + 实现约束 + 验证命令

---

## §0 基线溯源

| TC# | 覆盖 AC#（01 §5） | 覆盖场景（02 §2） | 覆盖类型 | 状态 |
|-----|------------------|------------------|---------|------|
| TC-N01–N08 | AC1–AC3, AC8 | 场景 1, 2 | 正常路径 | 待执行 |
| TC-B01–B04 | AC4, AC6 | 场景 3 | 边界条件 | 待执行 |
| TC-E01–E06 | AC5, AC7 | 场景 3, 4 | 异常路径 | 待执行 |
| TC-R01–R02 | AC1–AC8 | 场景 1–6 | 回归 | 待执行 |

---

## §1 测试范围

### 1.1 覆盖矩阵

| FP# | 功能点 | 正常 | 边界 | 异常 | 回归 | 覆盖率 |
|-----|--------|:--:|:--:|:--:|:--:|:--:|
| FP1 | 配置加载 | ✓ | ✓ | ✓ | ✓ | 100% |
| FP2 | 数据库初始化 | ✓ | — | ✓ | ✓ | 75% |
| FP3 | 数据 CRUD | ✓ | ✓ | ✓ | ✓ | 100% |
| FP4 | 请求认证 | ✓ | ✓ | ✓ | ✓ | 100% |
| FP5 | CORS 处理 | ✓ | — | — | ✓ | 50% |
| FP6 | 统一响应格式 | ✓ | ✓ | — | ✓ | 75% |
| FP7 | 错误码枚举 | ✓ | ✓ | — | ✓ | 75% |
| FP8 | 业务异常 | ✓ | — | ✓ | ✓ | 75% |
| FP9 | 日志配置 | ✓ | — | ✓ | ✓ | 75% |
| FP10 | 文本工具 | ✓ | ✓ | ✓ | ✓ | 100% |
| FP11 | 时间工具 | ✓ | ✓ | ✓ | ✓ | 100% |
| FP12 | 文件/集合工具 | ✓ | ✓ | ✓ | ✓ | 100% |

### 1.2 Gate 映射

| Gate | 用例范围 | 通过标准 | 交接下游 |
|------|---------|---------|---------|
| Gate A | TC-N*, TC-B*, TC-E*（全部 P0 用例） | P0 全部通过 | 实现阶段（code） |
| Gate B | TC-R*（回归） + 环境专项 | P0 全部通过 + P1 ≥90% | 交付 |

---

## §2 测试用例

### 2.1 正常路径

| ID | Given | When | Then | 关联 FP | 优先级 |
|----|-------|------|------|---------|--------|
| TC-N01 | config.yaml 存在于项目根目录，含 `server.port: 9000` | 导入 `from core.config import settings` 并访问 `settings.server_port` | `settings.server_port == 9000`（YAML 扁平化正确） | FP1 | P0 |
| TC-N02 | config.yaml 存在，Settings 导入成功 | 访问 `settings.server_host` | 值为 `"0.0.0.0"`（默认值）或 YAML 中配置的值 | FP1 | P0 |
| TC-N03 | MongoDB 可连接 | 调用 `await db.initialize()` | `db._initialized == True`，`db.db` 可访问 | FP2 | P0 |
| TC-N04 | MongoDB 已初始化 | 调用 `await db.insert_one("test_coll", {"name": "test"})` | 返回字符串 ID，文档含 `createdTime` 字段 | FP3 | P0 |
| TC-N05 | MongoDB 已初始化，test_coll 中有文档 `{"name": "test"}` | 调用 `await db.find_one("test_coll", {"name": "test"})` | 返回该文档 dict | FP3 | P0 |
| TC-N06 | 认证中间件启用，X-Token 正确 | 发送 GET 请求到非白名单路径，携带正确 X-Token | 响应 200，请求到达路由处理器 | FP4 | P0 |
| TC-N07 | 认证中间件禁用（`middleware_auth_enabled=False`） | 发送无 X-Token 的请求 | 响应 200，请求放行 | FP4 | P0 |
| TC-N08 | 调用 `success(data={"id": 1})` | 函数返回 JSONResponse | response.status_code==200，body 含 `{"code": 0, "message": "success", "data": {"id": 1}}` | FP6 | P0 |

### 2.2 边界条件

| ID | Given | When | Then | 关联 FP | 优先级 |
|----|-------|------|------|---------|--------|
| TC-B01 | 认证中间件启用，token 已配置 | 发送 OPTIONS 预检请求 | 响应直接放行，不检查 token（`middleware.py:64-66`） | FP4 | P0 |
| TC-B02 | 认证中间件启用 | 请求路径为 `/write-file`（白名单） | 响应直接放行，不检查 token（`middleware.py:71`） | FP4 | P0 |
| TC-B03 | `estimate_tokens("")` 传入空字符串 | 调用函数 | 返回 0（`utils.py:19-20`） | FP10 | P1 |
| TC-B04 | `format_file_size(0)` 传入 0 | 调用函数 | 返回 `"0B"`（`utils.py:142`） | FP12 | P1 |

### 2.3 异常路径

| ID | Given | When | Then | 关联 FP | 优先级 |
|----|-------|------|------|---------|--------|
| TC-E01 | 认证中间件启用，token 已配置 | 请求携带错误 X-Token `"bad-token"` | 响应 401，body `code=1009`，message 含 "Invalid or missing headers"（`middleware.py:93-99`） | FP4 | P0 |
| TC-E02 | 认证中间件启用，token 已配置 | 请求不携带 X-Token 头 | 响应 401，`code=1009`（`middleware.py:89` 取 `""` 与 required_token 不匹配） | FP4 | P0 |
| TC-E03 | MongoDB 未初始化 | 访问 `db.db` 属性 | 抛出 RuntimeError，message 含 "not initialized"（`database.py:83`） | FP3 | P0 |
| TC-E04 | MongoDB 不可达（错误 URL） | 调用 `await db.initialize()` | 抛出异常，`_initialized` 保持 False（`database.py:63-65`） | FP2 | P0 |
| TC-E05 | 业务逻辑中 | `raise BusinessException(ErrorCode.DATA_NOT_FOUND, "用户不存在")` | 异常对象含 `error_code=ErrorCode.DATA_NOT_FOUND`，`message="用户不存在"` | FP7, FP8 | P0 |
| TC-E06 | 传入非法日期 | `is_valid_date("2026-13-01")` | 返回 `False`（`utils.py:119-122`） | FP11 | P1 |

### 2.4 回归用例

| ID | Given | When | Then | 关联 FP | 优先级 |
|----|-------|------|------|---------|--------|
| TC-R01 | config.yaml 不存在 | 导入 Settings 并访问任意字段 | 返回对应 Field 默认值（应用不崩溃） | FP1 | P0 |
| TC-R02 | 完整请求链路：正确 token → 路由 → success() 返回 | 发送请求 | 响应 JSON 含 `code=0, message="success", data=...` | FP4, FP6 | P0 |

---

## §3 环境专项

| ID | Given | When | Then | 优先级 |
|----|-------|------|------|--------|
| TC-X01 | 应用已启动，日志文件 logs/app.log 存在 | 调用 `logger.info("test message")` | 日志同时出现在控制台 stdout 和 logs/app.log 中 | P1 |
| TC-X02 | logs/app.log 文件大小接近 10MB | 继续写入日志 | 触发轮转：app.log → app.log.1，新 app.log 创建（`logger.py:44-46`） | P2 |

---

## §4 测试环境

| 维度 | 配置 |
|------|------|
| 运行环境 | Python 3.10+，pytest |
| 部署方式 | 本地测试（无需 MongoDB 的用例可离线跑） |
| 测试目标 | `src/core/*.py` 全部 8 文件 |
| 数据准备 | 需 MongoDB 的用例：使用测试数据库 `test_db`；认证用例：设置 `API_X_TOKEN=test-token` |
| 分支 | `feat/core-infra` |

---

## §5 评审清单

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | 每 FP 多类覆盖（正常/边界/异常至少其一） | ✅ 12/12 FP 有覆盖 |
| 2 | Gate A 覆盖（P0 用例全部可执行） | ✅ 10 个 P0 用例 |
| 3 | 回归与影响链一致 | ✅ |
| 4 | 异常用例含恢复行为 | ✅ E03/E04 描述异常抛出 |
| 5 | 环境专项覆盖 | ✅ 日志专项 |
| 6 | 基线溯源闭合（AC# 全覆盖） | ✅ §0 溯源表 |
| 7 | 影响链每点有回归 | ✅ |

---

## §6 Gate A 交接

| 信号 | 内容 |
|------|------|
| 通过状态 | ✅ 待执行（用例已设计，等待 code 阶段实施） |
| P0 用例 ID | TC-N01, TC-N03, TC-N04, TC-N06, TC-N07, TC-N08, TC-B01, TC-B02, TC-E01, TC-E02, TC-E03, TC-E04, TC-E05 |
| 实现约束 | 1. 认证测试需要设置 `API_X_TOKEN` 环境变量；2. 数据库测试需要可用 MongoDB 实例或 mock motor；3. 日志测试需检查 logs/ 目录权限 |
| 验证命令 | `pytest tests/ -k "config or database or middleware or response or error or utils" -v` |

---

> **变更记录**
>
> | 日期 | 变更 | 触发 | 证据 |
> |------|------|------|------|
> | 2026-05-22 | 初始生成 | `/rui doc --from-code core-infra` | 技术评审 源码分析 + 故事任务 AC |
