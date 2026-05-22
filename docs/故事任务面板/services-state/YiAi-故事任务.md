# YiAi-故事任务 — services-state

> 结构化状态存储子系统故事任务。覆盖状态 CRUD (StateStoreService)、技能执行记录 (SkillRecorder)、会话适配 (SessionAdapter) 3 个组件。
>
> **来源**：源码分析 `/rui doc --from-code services-state`
> **证据等级**：B（只读源码 + 静态分析）
> **项目类型**：backend

---

## 效果示意

```mermaid
flowchart LR
    NOW["当前状态<br/>State 服务无文档"]:::pain
    NOW --> GOAL["目标状态<br/>3 组件状态管理模型清晰"]:::goal

    classDef pain fill:#ffebee,stroke:#c62828;
    classDef goal fill:#e8f5e9,stroke:#2e7d32;
```

---

## §1 Story

### Story 1: 结构化状态存储（StateStoreService）

| 字段 | 内容 |
|------|------|
| 作为 | 系统开发者 |
| 我想要 | 统一的 CRUD 接口管理结构化状态记录 |
| 以便 | 各子系统能一致地存取状态数据，支持按类型/标签/时间等维度查询 |
| 优先级 | P0 |
| 范围边界 | MongoDB state_records 集合，单文档 CRUD + 分页查询 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 创建记录 | 子系统需要持久化状态 | 传入 record 字典 → 自动生成 key(UUID) → 补充时间戳 → insert_one | 返回 `{"key": "..."}` |
| 2 | 条件查询 | 运维或 API 查询历史记录 | 构建 filter（record_type/tags/title/时间范围）→ 排序 → 分页 → count_documents | 返回 list + total + 分页信息 |
| 3 | 获取单条 | 需要查看特定记录详情 | 按 key 查询 find_one | 返回完整记录或 None |
| 4 | 更新记录 | 记录内容需要修改 | 按 key 查找 → $set 更新 → 保护 key/created_time 不被覆盖 → 更新 updated_time | 返回确认信息 |
| 5 | 删除记录 | 记录不再需要 | 按 key 删除 → 检查 deleted_count | 返回确认或抛 ValueError |

---

### Story 2: 技能执行记录（SkillRecorder）

| 字段 | 内容 |
|------|------|
| 作为 | 技能执行管线 |
| 我想要 | 自动记录每次技能执行的耗时、状态和摘要 |
| 以便 | 追踪执行历史，分析性能和成功率 |
| 优先级 | P1 |
| 范围边界 | 基于 StateStoreService，fire-and-forget 模式，失败不阻断主流程 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 同步记录 | 技能执行完毕 | 构建 SkillExecutionRecord → 调用 state_service.create() | 记录写入 state_records |
| 2 | 异步 fire-and-forget | 不需要等待记录完成 | create_task(record(...)) → 立即返回 | 后台写入，不阻塞主流程 |
| 3 | 记录失败容错 | 数据库不可用或写入失败 | catch Exception → logger.error | 不抛异常，不阻断业务 |

---

### Story 3: 会话适配（SessionAdapter）

| 字段 | 内容 |
|------|------|
| 作为 | 数据迁移/查询模块 |
| 我想要 | 将遗留 sessions 集合文档转换为结构化 SessionState 模型 |
| 以便 | 新版代码可以用 Pydantic 模型操作历史会话数据 |
| 优先级 | P2 |
| 范围边界 | 只读适配，不修改原始 sessions 集合 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 单文档适配 | 需要读取单个遗留 session | 字段映射（pageContent→page_content 等）→ model_validate | 返回 SessionState 对象 |
| 2 | 批量适配 | 需要迁移大量历史数据 | 遍历 cursor → 逐条 adapt → 统计成功/失败 → 返回 AdaptationResult | 返回成功数/失败数/错误列表 |
| 3 | 适配容错 | 文档格式不符合预期 | model_validate 失败 → logger.warning → 回退到宽松构造 | 不阻断批量处理 |

---

## §2 Requirements

### 功能点

| FP# | 描述 | 组件 | 优先级 |
|-----|------|------|:---:|
| FP1 | 创建状态记录 — 自动生成 UUID key + 时间戳 | state_service | P0 |
| FP2 | 条件查询 — record_type/tags/title_contains/时间范围 + 分页 | state_service | P0 |
| FP3 | 单条查询 — 按 key 精确查找 | state_service | P1 |
| FP4 | 更新记录 — $set 更新，保护 key/created_time | state_service | P1 |
| FP5 | 删除记录 — 按 key 删除，不存在时抛 ValueError | state_service | P1 |
| FP6 | 技能执行记录 — SkillExecutionRecord 模型验证 + 写入 | skill_recorder | P1 |
| FP7 | 异步 fire-and-forget — create_task 后台写入 | skill_recorder | P1 |
| FP8 | 会话适配 — 字段映射 + Pydantic 验证 + 宽松回退 | session_adapters | P2 |
| FP9 | 批量适配 — cursor 遍历 + 统计 + batch_size 进度日志 | session_adapters | P2 |

### 业务规则

| R# | 描述 | 证据级别 |
|----|------|:---:|
| R1 | 创建时 key 由 UUID 自动生成，也可由调用方指定 | A |
| R2 | 更新操作保护 key 和 created_time 字段不被覆盖 | A |
| R3 | 查询 page_size 受 max_limit(8000) 上限约束 | A |
| R4 | title_contains 使用正则模糊匹配（$regex + $options: "i"） | A |
| R5 | SkillRecorder 任何异常不抛出，仅 logger.error | A |
| R6 | SessionAdapter 验证失败时先尝试 model_validate，失败后回退宽松构造 | A |
| R7 | 批量适配每 100 条输出进度日志 | A |

---

## §3 成功标准

| SC# | 描述 | 优先级 |
|-----|------|:---:|
| SC1 | 创建记录后返回有效的 UUID key | P0 |
| SC2 | 条件查询返回分页结果，total 与实际匹配 | P0 |
| SC3 | 更新不存在的 key 时抛 ValueError | P1 |
| SC4 | SkillRecorder 写入失败时不抛异常 | P1 |

---

## §4 范围边界

**范围内**：StateStoreService CRUD、SkillRecorder 记录、SessionAdapter 适配
**范围外**：sessions 集合写入（只读适配）、state_records 集合 schema 迁移

---

## §5 AC

| AC# | Given | When | Then | 门禁 |
|-----|-------|------|------|------|
| AC1 | state_records 集合为空 | create(record) | 返回 `{"key": "<uuid>"}`，记录含 created_time/updated_time | Gate A |
| AC2 | 存在多条记录 | query(record_type="skill_execution") | 返回该类型的 list + total + 分页 | Gate A |
| AC3 | key 不存在 | update(key, data) | ValueError("Record not found") | Gate A |
| AC4 | 数据库写入异常 | SkillRecorder.record(...) | logger.error，不抛异常 | Gate A |

---

### 主要价值

- 📊 **统一状态存储** — 单一 StateStoreService 提供完整 CRUD，全系统复用
- 📝 **执行可追踪** — SkillRecorder 自动记录技能执行，fire-and-forget 不阻塞
- 🔄 **兼容遗留数据** — SessionAdapter 平滑适配旧 sessions 集合
- 🛡️ **容错设计** — 记录失败不抛异常，适配失败有宽松回退

---

## 回溯链

| 来源 | 路径 | 证据级别 |
|------|------|---------|
| 源码 | `src/services/state/` (3 文件) | A |
| 依赖 | `src/models/schemas.py` — SessionState/SkillExecutionRecord/AdaptationResult | A |
| 依赖 | `src/core/config.py` — state_store_query_max_limit/collection_state_records | A |

### 变更记录

| 日期 | 版本 | 变更内容 | 来源 |
|------|------|---------|------|
| 2026-05-22 | 1.0.0 | 初始文档基线 | /rui doc --from-code services-state |
