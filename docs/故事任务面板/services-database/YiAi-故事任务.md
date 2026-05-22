# YiAi-故事任务 — services-database

> 数据服务层故事任务文档。覆盖 `data_service.py` + `mongo_store.py` 两个数据访问实现。
>
> **来源**：源码分析 `/rui doc --from-code services-database`
> **证据等级**：B（只读源码 + 静态分析）
> **项目类型**：backend

---

## 效果示意

```mermaid
flowchart LR
    NOW["当前状态<br/>数据访问层无文档基线<br/>双实现语义不明确"]:::pain
    NOW --> M1["里程碑 1<br/>故事任务基线建立<br/>7 大操作 + 双实现梳理"]:::milestone
    M1 --> M2["里程碑 2<br/>使用场景覆盖<br/>查询/CRUD/去重/聚合"]:::milestone
    M2 --> GOAL["目标状态<br/>数据服务层文档完整<br/>调用方有明确契约参照"]:::goal

    classDef pain fill:#ffebee,stroke:#c62828;
    classDef milestone fill:#fff3e0,stroke:#e65100;
    classDef goal fill:#e8f5e9,stroke:#2e7d32;
```

---

## §1 Story

### Story 1: 通用数据查询

| 字段 | 内容 |
|------|------|
| 作为 | 前端开发者或 API 调用方 |
| 我想要 | 通过灵活的参数化查询接口检索任意集合的数据 |
| 以便 | 无需为每种查询场景编写专用后端接口 |
| 优先级 | P0 |
| 范围边界 | 只支持已存在的 MongoDB 集合，不创建新集合 |
| 依赖 | MongoDB 连接可用，`db` 单例已初始化 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 分页查询集合数据 | 调用 `query_documents` 传入 collection_name + pageNum/pageSize | 构建 filter → 执行 find → 返回分页结果 | 返回 {list, total, pageNum, pageSize, totalPages} |
| 2 | 字段投影查询 | 调用时传入 fields 或 excludeFields 参数 | 构建 projection → 排除 _id → 返回指定字段 | 返回仅含指定字段的文档列表 |
| 3 | 日期范围查询 | 传入 isoDate 参数（单个日期或逗号分隔的日期范围） | 构建多格式日期正则 → 匹配 pubDate/published/isoDate 字段 | 返回日期范围内文档 |
| 4 | 模糊搜索 | 传入字符串参数（逗号分隔多关键词） | re.escape → 构建 $or regex → 执行查询 | 返回匹配关键词的文档 |
| 5 | 数值/日期范围过滤 | 传入 [start, end] 双元素数组 | 判定类型 → $gte/$lt → 执行查询 | 返回范围内的文档 |
| 6 | 列表精确匹配 | 传入 >2 元素数组 | 构建 $in 条件 → 执行查询 | 返回匹配列表中任意值的文档 |
| 7 | sessions 自动排除 pageContent | 查询 sessions 集合时 | 自动在 projection 中排除 pageContent | 返回数据不含 pageContent 大字段 |

---

### Story 2: 文档 CRUD 生命周期

| 字段 | 内容 |
|------|------|
| 作为 | 数据管理员或自动化脚本 |
| 我想要 | 通过统一接口创建、读取、更新、删除文档 |
| 以便 | 数据生命周期管理有统一入口和约束 |
| 优先级 | P0 |
| 范围边界 | 仅操作已存在的集合，不修改集合结构 |
| 依赖 | Story 1 查询能力 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 创建文档 | 调用 `create_document` 传入 collection_name + data | 验证集合名 → RSS link 去重检查 → 生成 key/uuid + 时间戳 + order → insert | 返回 {key} |
| 2 | 查询单文档详情 | 调用 `get_document_detail` 传入 collection_name + id | 验证参数 → find_one by key → 返回文档 | 返回完整文档（sessions 排除 pageContent） |
| 3 | 更新文档 | 调用 `update_document` 传入 collection_name + data（含 key） | 验证 key 存在 → 移除不可变字段 → $set 更新 + updatedTime | 返回 {key, updated: true} |
| 4 | 删除文档 | 调用 `delete_document` 传入 collection_name + key | 验证参数 → delete_one → 检查 deleted_count | 返回 {key, deleted: true} 或抛异常 |
| 5 | 创建或更新（upsert） | 调用 `upsert_document` 传入 collection_name + filter + update | 构建 $set/$setOnInsert → update_one(upsert=True) | 返回 {matched_count, modified_count, upserted_id} |

---

### Story 3: 数据完整性与唯一性保障

| 字段 | 内容 |
|------|------|
| 作为 | 系统运维人员 |
| 我想要 | 关键字段（RSS link）在创建和更新时自动进行唯一性校验 |
| 以便 | 防止重复数据污染内容库 |
| 优先级 | P0 |
| 范围边界 | 当前仅对 RSS 集合的 link 字段强制唯一性 |
| 依赖 | Story 2 CRUD 操作 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | RSS 创建去重 | 创建 RSS 文档且 data 含 link | find_one 检查 link → 存在则抛异常 → 不存在则创建 | 重复 link 时阻断并提示 |
| 2 | RSS 更新去重 | 更新 RSS 文档且 data 含新 link | find_one 检查新 link → 存在且 key 不同则抛异常 → 否则更新 | 跨文档 link 冲突时阻断 |
| 3 | contentHash 自动生成 | 更新 RSS 文档且 data 含 content | hashlib.md5(content) → 写入 contentHash | 自动生成内容指纹 |
| 4 | 重复 key 错误处理 | insert 触发 MongoDB E11000 | 捕获异常 → 区分 RSS link 冲突 vs 其他唯一约束 | 返回明确错误信息 |

---

### Story 4: 故事任务面板目录查询

| 字段 | 内容 |
|------|------|
| 作为 | 故事面板前端或面板管理器 |
| 我想要 | 查询 sessions 集合中所有故事任务面板的项目和故事目录列表 |
| 以便 | 故事面板概览页能展示所有项目的故事目录树 |
| 优先级 | P1 |
| 范围边界 | 只读 sessions 集合，按 projectName + storyName 去重聚合 |
| 依赖 | sessions 集合中存在含 projectName 字段的文档 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 查询全部故事目录 | 调用 `list_story_task_dirs` 无过滤参数 | MongoDB aggregation: $match → $group → $sort → $skip/$limit | 返回 {list: [{project_name, story_name, dir_path, session_count, latest_time}], total, ...} |
| 2 | 按项目过滤 | 调用时传入 project_name 参数 | $match 阶段添加 projectName 过滤 | 仅返回指定项目的目录 |
| 3 | 分页查询 | 传入 page_num/page_size | aggregation 管道中 $skip/$limit | 支持大量目录分页加载 |

---

## §2 Requirements

### 功能点

| FP# | 描述 | 输入 | 输出 | 错误行为 | 优先级 |
|-----|------|------|------|---------|--------|
| FP1 | 灵活过滤查询 — 支持精确匹配、模糊搜索、日期范围、数值范围、列表 $in | collection_name + query_params | 分页文档列表 + total | 无效分页参数时抛 ValueError | P0 |
| FP2 | 字段投影 — fields 指定返回字段或 excludeFields 排除字段 | fields 或 excludeFields 字符串 | 投影后的文档列表 | sessions 自动排除 pageContent | P0 |
| FP3 | 日期过滤器 — isoDate 参数支持单日或日期范围，自动匹配多日期格式 | isoDate 字符串 | 匹配 pubDate/published/isoDate 的文档 | 无效日期格式时跳过日期过滤 | P0 |
| FP4 | 安全模糊搜索 — 用户输入自动 re.escape 转义特殊字符 | 字符串搜索词 | 正则匹配结果 | 特殊字符被当作字面量处理 | P0 |
| FP5 | 创建文档 — 自动生成 key/uuid + createdTime/updatedTime + order | collection_name + data | {key} | link 重复时抛 ValueError；E11000 时抛明确错误 | P0 |
| FP6 | 更新文档 — 按 key 更新，保护不可变字段 | collection_name + data(含 key) | {key, updated: true} | key 不存在时抛 ValueError | P0 |
| FP7 | Upsert 文档 — 原子 $set/$setOnInsert，自动生成 key + 时间戳 | collection_name + filter + update | {matched_count, modified_count, upserted_id} | 缺少必填参数时抛 ValueError | P0 |
| FP8 | 删除文档 — 按 key 删除并验证结果 | collection_name + key | {key, deleted: true} | deleted_count=0 时抛 ValueError | P0 |
| FP9 | RSS link 唯一性 — 创建/更新时检测 link 重复并阻断 | RSS 集合 + link 字段 | 正常创建/更新 或 ValueError | link 已存在时阻断 | P0 |
| FP10 | sessions pageContent 保护 — 自动从查询/创建/更新中排除 pageContent | sessions 集合名 | 不含 pageContent 的结果 | — | P1 |
| FP11 | 故事目录聚合查询 — 从 sessions 中按 projectName+storyName 分组去重 | project_name(可选) + 分页参数 | {list: [{project_name, story_name, dir_path, session_count, latest_time}], total} | — | P1 |
| FP12 | 双实现兼容 — data_service(函数式/params 接口) + mongo_store(类式/类型化接口) | 按调用方选择 | 相同语义、不同接口风格 | — | P1 |
| FP13 | 排序链 — 主排序字段 + updatedTime DESC + createdTime DESC | orderBy + orderType | 排序后的结果 | orderBy='order' 时固定升序 | P1 |

### 业务规则

| R# | 描述 | 校验方式 | 证据级别 |
|----|------|---------|---------|
| R1 | 所有数据库操作前必须调用 `db.initialize()` 或 `ensure_initialized()` | 代码审查：每个公共方法首行 | A |
| R2 | key 字段使用精确匹配，不使用模糊搜索 | `_build_filter()`:128–140 — key 直接赋值 | A |
| R3 | pageSize 上限 8000，防止单次查询拉取过多数据 | `query_documents()`:213 — `min(8000, ...)` | A |
| R4 | RSS link 创建和更新时均需唯一性校验 | `create_document()`:310–315 + `update_document()` (mongo_store):433–444 | A |
| R5 | sessions 集合查询时默认排除 pageContent 字段 | `query_documents()`:230,237,240–241 | A |
| R6 | 创建文档时自动分配 order = max_order + 1 | `create_document()`:328–336 | A |
| R7 | 更新文档时不可修改 _id / key / createdTime | `update_document()`:376–379 — pop 移除 | A |
| R8 | 用户输入搜索词必须经过 re.escape 转义防止 NoSQL 注入 | `_handle_string_search_filter()`:118,123,127 | A |

### 数据约束

| 约束 | 类型 | 范围/格式 | 来源 |
|------|------|----------|------|
| collection_name | string | 非空字符串，必须对应已存在的 MongoDB 集合 | `_validate_collection_name()` |
| key | string | UUID v4 格式，创建时自动生成 | `str(uuid.uuid4())` |
| pageNum | int | ≥1 | `max(1, int(...))` |
| pageSize | int | 1–8000 | `min(8000, max(1, int(...)))` |
| createdTime / updatedTime | string | `YYYY-MM-DD HH:MM:SS` UTC | `get_current_time()` / `get_current_time()` |
| order | int | 自增整数，创建时 = max_order + 1 | `create_document()` |
| contentHash | string | MD5 hex digest (32 chars) | `hashlib.md5(content).hexdigest()` |

---

## §3 成功标准

| SC# | 描述 | 度量方式 | 目标值 | 优先级 | 关联 FP# |
|-----|------|---------|--------|--------|---------|
| SC1 | 查询接口支持所有过滤类型 | 覆盖精确/模糊/日期/范围/列表 | 5 种过滤全部可用 | P0 | FP1,FP3,FP4 |
| SC2 | CRUD 完整生命周期无数据丢失 | 创建→读取→更新→删除 全流程测试 | 数据一致性 100% | P0 | FP5–FP8 |
| SC3 | RSS link 重复 100% 阻断 | 并发创建同 link 测试 | 0 穿透 | P0 | FP9 |
| SC4 | NoSQL 注入特殊字符被安全转义 | 传入 `.*` / `$regex` / `(` 等字符 | 全部按字面量匹配 | P0 | FP4 |
| SC5 | sessions 查询不返回 pageContent | 查询 sessions 集合后检查返回字段 | 0 次泄露 | P1 | FP10 |

---

## §4 范围边界

### 范围内

| # | 条目 | 关联 FP# | 边界说明 |
|---|------|---------|---------|
| 1 | 通用查询过滤引擎 | FP1–FP4 | 支持精确/模糊/日期/范围/列表 5 种过滤 |
| 2 | 文档 CRUD 操作 | FP5–FP8 | 创建/读取/更新/删除/upsert 完整生命周期 |
| 3 | RSS 数据完整性保障 | FP9 | link 唯一性校验 + contentHash 生成 |
| 4 | sessions 集合优化 | FP10 | pageContent 自动排除 |
| 5 | 故事目录聚合查询 | FP11 | sessions 集合聚合管道 |

### 范围外

| # | 条目 | 排除原因 | 替代方案 |
|---|------|---------|---------|
| 1 | 数据库集合创建/删除 | 属于数据库管理层面 | 使用 MongoDB 管理工具 |
| 2 | 索引管理 | 性能优化属于运维层面 | DBA 手动创建索引 |
| 3 | 事务支持 | 当前未使用 MongoDB 事务 | 单文档操作保证原子性 |
| 4 | 数据迁移/备份 | 属于运维层面 | mongodump/mongorestore |

---

## §5 AC

| AC# | Given | When | Then | 门禁 |
|-----|-------|------|------|------|
| AC1 | 存在 rss 集合含多条数据 | 调用 query_documents(collection_name='rss', title='测试') | 返回 title 含"测试"的文档列表 | Gate A |
| AC2 | 提供 collection_name + data | 调用 create_document | 返回 {key}，文档写入数据库且 order 自动分配 | Gate A |
| AC3 | 存在 key=xxx 的文档 | 调用 update_document 修改 title | 文档 title 更新，updatedTime 刷新，key/createdTime 不变 | Gate A |
| AC4 | 存在 key=xxx 的文档 | 调用 delete_document(key=xxx) | 文档被删除，再次查询返回空 | Gate A |
| AC5 | RSS 已存在 link=A | 创建新文档 link=A | 抛出 ValueError 提示 link 重复 | Gate A |
| AC6 | 传入搜索词 `test.*$(`) | 调用 query_documents 模糊搜索 | 搜索词被 re.escape 转义，按字面量匹配 | Gate A |
| AC7 | sessions 集合有含 projectName+storyName 的文档 | 调用 list_story_task_dirs() | 返回按项目/故事去重的目录列表 | Gate A |
| AC8 | 传入 filter + update | 调用 upsert_document | 存在则更新（matched_count≥1），不存在则插入（upserted_id 非空） | Gate A |

---

## §6 风险与假设

| # | 风险/假设 | 类型 | 可能性 | 影响 | 缓解/验证策略 | 关联 FP# |
|---|----------|------|--------|------|-------------|---------|
| 1 | data_service 和 mongo_store 双实现行为不一致 | 风险 | M | H | 对照两个文件的同名方法签名和边界处理，差异处标注 | FP12 |
| 2 | 大集合无索引查询导致性能下降 | 风险 | H | M | pageSize 上限 8000 + 提示 DBA 建立查询字段索引 | FP1 |
| 3 | sessions pageContent 字段在某些路径未被排除 | 风险 | L | M | data_service 有多层保护（fields/exclude/默认），mongo_store 缺少此逻辑 | FP10 |
| 4 | RSS link 唯一性在并发下存在竞态窗口 | 风险 | L | M | find + insert 之间无原子保证，建议加 unique index | FP9 |
| 5 | MongoDB 连接池正常且 db 单例初始化正确 | 假设 | — | — | 每个公共方法首行调用 initialize | FP1–FP11 |

---

### 主要价值

- 🎯 **统一数据访问** — 7 大通用操作覆盖全部数据访问需求，调用方无需直接操作 MongoDB 驱动
- 🛡️ **安全过滤引擎** — 用户输入自动 re.escape 转义，防止 NoSQL 注入；RSS link 唯一性校验防止重复数据
- 📄 **智能字段投影** — sessions 集合自动排除 pageContent 大字段，减少网络传输和内存开销
- 🔄 **双实现兼容** — 函数式（executor 调用）+ 类式（直接导入）两种接口风格，适应不同调用场景
- 📊 **聚合查询能力** — list_story_task_dirs 通过 MongoDB aggregation pipeline 高效去重统计

---

## 回溯链

| 来源 | 路径 | 证据级别 |
|------|------|---------|
| 源码 | `src/services/database/data_service.py` (540 lines) | A |
| 源码 | `src/services/database/mongo_store.py` (535 lines) | A |
| 依赖 | `src/core/database.py` — db 单例 + CRUD 包装 | B |
| 依赖 | `src/core/config.py` — collection_sessions / collection_rss 配置 | B |

### 变更记录

| 日期 | 版本 | 变更内容 | 来源 |
|------|------|---------|------|
| 2026-05-22 | 1.0.0 | 初始文档基线，从源码反推生成 | /rui doc --from-code services-database |
