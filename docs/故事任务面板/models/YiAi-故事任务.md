# YiAi-故事任务 — models

> 数据模型层故事任务。覆盖 Pydantic 请求/响应模型 (schemas)、MongoDB 集合常量 (collections) 2 个组件。
>
> **来源**：源码分析 `/rui doc --from-code models`
> **证据等级**：B（只读源码 + 静态分析）
> **项目类型**：backend

---

## 效果示意

```mermaid
flowchart LR
    NOW["当前状态<br/>Models 层无文档"]:::pain
    NOW --> GOAL["目标状态<br/>15 请求模型 + 4 状态模型 + 8 集合常量 清晰"]:::goal

    classDef pain fill:#ffebee,stroke:#c62828;
    classDef goal fill:#e8f5e9,stroke:#2e7d32;
```

---

## §1 Story

### Story 1: API 请求/响应模型（schemas）

| 字段 | 内容 |
|------|------|
| 作为 | API 开发者 |
| 我想要 | 统一的 Pydantic 模型定义所有请求参数和状态记录结构 |
| 以便 | FastAPI 自动校验参数、生成 OpenAPI 文档，且各层使用一致的数据结构 |
| 优先级 | P0 |
| 范围边界 | 15 请求模型（执行/文件/RSS/企业微信/状态查询）+ 4 状态模型 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 请求校验 | API 收到 HTTP 请求 | FastAPI 自动按模型校验 body → 失败返回 422 | 合法参数传入路由函数 |
| 2 | 模块执行请求 | 客户端发送 ExecuteRequest | 校验 module_name/method_name/parameters | 参数传入 executor |
| 3 | 文件操作请求 | 客户端发送 FileReadRequest 等 | 校验 target_file/content/is_base64 等字段 | 参数传入文件服务 |
| 4 | RSS 解析请求 | 客户端发送 ParseRssRequest | 校验 URL 格式 | 参数传入 RSS 服务 |
| 5 | 状态查询请求 | 客户端发送 StateQueryRequest | 校验分页范围(ge=1, le=8000) | 参数传入 StateStoreService |

---

### Story 2: 集合常量（collections）

| 字段 | 内容 |
|------|------|
| 作为 | 数据库操作层 |
| 我想要 | 集中管理所有 MongoDB 集合名称常量 |
| 以便 | 避免硬编码字符串分散在各服务中，防止拼写错误 |
| 优先级 | P1 |
| 范围边界 | 8 个集合名常量，纯字符串定义 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 引用集合名 | 服务需要访问 MongoDB 集合 | `from models.collections import SESSIONS` → 使用常量 | 编译期即可发现拼写错误 |
| 2 | 新增集合 | 新功能需要新集合 | 在 collections.py 添加常量 → 更新 __init__.py 导出 | 全系统一致引用 |

---

## §2 Requirements

### 功能点

| FP# | 描述 | 组件 | 优先级 |
|-----|------|------|:---:|
| FP1 | ExecuteRequest — 模块执行参数校验（module_name/method_name/parameters） | schemas | P0 |
| FP2 | FileUploadRequest — 文件上传参数（filename/content/is_base64/target_dir） | schemas | P0 |
| FP3 | FileReadRequest/FileWriteRequest/FileDeleteRequest — 文件 CRUD 参数 | schemas | P1 |
| FP4 | FileRenameRequest/FolderRenameRequest/FolderDeleteRequest — 文件组织参数 | schemas | P1 |
| FP5 | ImageUploadToOssRequest — OSS 图片上传参数（data_url/filename/directory） | schemas | P1 |
| FP6 | ParseRssRequest/ParseAllRssRequest — RSS 解析参数 | schemas | P1 |
| FP7 | SchedulerConfigRequest — RSS 调度器配置（enabled/type/interval/cron） | schemas | P1 |
| FP8 | WeWorkWebhookRequest — 企业微信 Webhook 参数 | schemas | P2 |
| FP9 | StateRecord/SessionState/SkillExecutionRecord — 状态存储模型 | schemas | P1 |
| FP10 | StateQueryRequest — 状态查询参数（5 维度过滤 + 分页） | schemas | P1 |
| FP11 | AdaptationResult — 批量适配统计结果 | schemas | P2 |
| FP12 | 集合名常量 — SESSIONS/RSS/CHAT_RECORDS 等 8 个 | collections | P1 |

### 业务规则

| R# | 描述 | 证据级别 |
|----|------|:---:|
| R1 | 所有文件操作请求模型 target_dir/target_file 为必填字段 | A |
| R2 | SkillExecutionRecord.status 限 success/failed/timeout/cancelled 四值 | A |
| R3 | StateQueryRequest.page_size 范围 ge=1, le=8000 | A |
| R4 | SkillExecutionRecord.duration_ms 范围 ge=0 | A |
| R5 | input_summary/output_summary 上限 2000 字符，error_message 上限 4000 字符 | A |

---

## §3 成功标准

| SC# | 描述 | 优先级 |
|-----|------|:---:|
| SC1 | ExecuteRequest 含空字符串默认值时不抛异常 | P0 |
| SC2 | SkillExecutionRecord 含无效 status 值时 ValidationError | P1 |
| SC3 | StateQueryRequest page_size 超 8000 时 ValidationError | P1 |
| SC4 | 所有集合名常量可通过 models.collections 导入 | P1 |

---

## §4 范围边界

**范围内**：schemas.py 全部 Pydantic 模型、collections.py 全部常量
**范围外**：模型运行时行为（属于使用方服务）、ORM 映射

---

## §5 AC

| AC# | Given | When | Then | 门禁 |
|-----|-------|------|------|------|
| AC1 | parameters 字段未传 | ExecuteRequest() | module_name="" method_name="" parameters={} | Gate A |
| AC2 | status="invalid" | SkillExecutionRecord(skill_name="x", status="invalid", duration_ms=1.0) | ValidationError | Gate A |
| AC3 | page_size=9000 | StateQueryRequest(page_size=9000) | ValidationError | Gate A |
| AC4 | 导入 SESSIONS | from models.collections import SESSIONS | 值为 "sessions" | Gate A |

---

### 主要价值

- ✅ **统一校验** — 15 请求模型覆盖全部 API，FastAPI 自动校验 + OpenAPI 文档
- 📊 **状态模型** — 4 个 Pydantic 模型标准化状态数据结构
- 🏷️ **集合常量** — 8 个集合名集中管理，消除魔法字符串
- 🔒 **字段约束** — min_length/ge/le/pattern/max_length 多层约束防非法输入

---

## 回溯链

| 来源 | 路径 | 证据级别 |
|------|------|---------|
| 源码 | `src/models/schemas.py` (192 行) | A |
| 源码 | `src/models/collections.py` (10 行) | A |
| 源码 | `src/models/__init__.py` (51 行) | A |

### 变更记录

| 日期 | 版本 | 变更内容 | 来源 |
|------|------|---------|------|
| 2026-05-22 | 1.0.0 | 初始文档基线 | /rui doc --from-code models |
