# YiAi-故事任务 — services-rss

> RSS 订阅服务层故事任务文档。覆盖 `feed_service.py`（RSS 抓取解析） + `rss_scheduler.py`（定时调度管理）。
>
> **来源**：源码分析 `/rui doc --from-code services-rss`
> **证据等级**：B（只读源码 + 静态分析）
> **项目类型**：backend

---

## 效果示意

```mermaid
flowchart LR
    NOW["当前状态<br/>RSS 服务无文档基线<br/>抓取+调度逻辑不透明"]:::pain
    NOW --> M1["里程碑 1<br/>故事任务基线建立<br/>3 大核心流程梳理"]:::milestone
    M1 --> M2["里程碑 2<br/>完整文档基线<br/>使用场景+技术评审+测试+安全"]:::milestone
    M2 --> GOAL["目标状态<br/>RSS 服务文档完整<br/>运维和调用方有清晰参照"]:::goal

    classDef pain fill:#ffebee,stroke:#c62828;
    classDef milestone fill:#fff3e0,stroke:#e65100;
    classDef goal fill:#e8f5e9,stroke:#2e7d32;
```

---

## §1 Story

### Story 1: RSS 源抓取与解析

| 字段 | 内容 |
|------|------|
| 作为 | 内容运营人员或自动化系统 |
| 我想要 | 从外部 RSS 源地址抓取并解析内容 |
| 以便 | 将外部资讯自动汇聚到系统中 |
| 优先级 | P0 |
| 范围边界 | 仅处理 HTTP GET 可访问的 RSS/Atom 源，最大 10MB |
| 依赖 | 外部 RSS 源可访问，aiohttp + feedparser 可用 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 解析单个 RSS 源 | 调用 `parse_feed` 传入 url | HTTP GET 流式读取 → feedparser 解析 → 逐条目去重入库 | 返回 {success, url, source, saved_count, updated_count, total_items} |
| 2 | 批量解析全部启用源 | 调用 `parse_all_enabled_rss_sources` | 从 seeds 集合查询启用的源 → 并发解析（最多 3 个） | 返回 {total_sources, success_count, failed_count, results} |
| 3 | 安全解析单个源 | 调用 `parse_rss_source_safe` 传入 url + name | 委托 process_feed_from_url 处理 | 返回结果字典（含 error 字段） |

---

### Story 2: RSS 条目去重入库

| 字段 | 内容 |
|------|------|
| 作为 | 数据管理员 |
| 我想要 | RSS 条目按 link 去重，已存在的自动更新而非重复创建 |
| 以便 | 避免重复内容污染数据库，同时保持已有条目的 key 和创建时间不变 |
| 优先级 | P0 |
| 范围边界 | 仅对 RSS 集合按 link 字段去重 |
| 依赖 | Story 1 抓取流程 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 新条目创建 | link 在 RSS 集合中不存在 | insert_one 写入，自动生成 key + createdTime + updatedTime | saved_count +1 |
| 2 | 已有条目更新 | link 已存在 | 保留原 key 和 createdTime，update_one 更新其他字段 | updated_count +1（modified_count > 0 时） |
| 3 | 无 link 条目跳过 | entry 无 link 字段 | `continue` 跳过该条目 | 不计入 total_items |

---

### Story 3: RSS 定时调度

| 字段 | 内容 |
|------|------|
| 作为 | 系统运维人员 |
| 我想要 | 配置 RSS 定时抓取任务（间隔或 Cron 模式），并随时启停 |
| 以便 | RSS 内容自动更新无需手动干预 |
| 优先级 | P0 |
| 范围边界 | 单进程内调度器，不涉及分布式调度 |
| 依赖 | APScheduler（AsyncIOScheduler），seeds 集合中存在启用的 RSS 源 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 启动定时任务 | 调用 `start_rss_scheduler` | 创建/获取 AsyncIOScheduler → 移除旧任务 → 按配置添加新任务 → 启动调度器 | 调度器开始按周期执行 |
| 2 | 停止定时任务 | 调用 `stop_rss_scheduler` | shutdown scheduler → 置空引用 → _running = False | 调度器停止，不再触发解析 |
| 3 | 设置间隔模式 | 调用 `set_scheduler_config` type=interval + interval 秒数 | 验证 interval ≥ 60 → 更新配置 → 重启调度器 | 按新间隔执行 |
| 4 | 设置 Cron 模式 | 调用 `set_scheduler_config` type=cron + cron 配置 | 验证字段范围 → 更新配置 → 重启调度器 | 按 Cron 表达式执行 |
| 5 | 查看调度器状态 | 调用 `get_scheduler_status_info` | 返回 {enabled, type, interval, cron} | 获取当前运行状态和配置 |

---

## §2 Requirements

### 功能点

| FP# | 描述 | 输入 | 输出 | 错误行为 | 优先级 |
|-----|------|------|------|---------|--------|
| FP1 | HTTP 流式抓取 RSS 源 — 分块读取（8KB），硬限制 10MB，超时 60s | url 字符串 | feedparser.FeedParserDict | HTTP 非 200 / Content-Length 超限 / 实际内容超限 / 网络错误 / 解析失败 → BusinessException | P0 |
| FP2 | RSS 条目数据提取 — 从 feed entry 构建入库数据 | feedparser entry + source_name + tags | {title, link, description, tags, source_name, source_url, published, ...} | 字段缺失时使用默认空值 | P0 |
| FP3 | Link 去重入库 — 按 link 查询，存在则更新、不存在则创建 | item_data（含 link） | saved_count / updated_count | 无 link 的条目跳过 | P0 |
| FP4 | 批量并发解析 — Semaphore 限制 3 并发，asyncio.gather 并行 | sources 列表 | {total_sources, success_count, failed_count, results} | 单个源失败不阻断其他源 | P0 |
| FP5 | 启用的 RSS 源查询 — 从 seeds 集合查询 enabled≠false 且 url 非空的源 | — | 源配置列表 | 查询失败返回空列表（不阻断） | P0 |
| FP6 | 间隔模式调度 — IntervalTrigger，最小间隔 60 秒 | interval 秒数 | 调度器按间隔执行 | interval < 60 抛 ValueError | P1 |
| FP7 | Cron 模式调度 — CronTrigger，支持秒/分/时/日/月/周 | cron 配置字典 | 调度器按 Cron 执行 | 字段范围无效抛 ValueError | P1 |
| FP8 | 动态配置热更新 — set_config 后自动 stop+start 重启调度器 | 新配置 | 调度器以新配置运行 | — | P1 |
| FP9 | RSS 系统初始化/关闭 — init_rss_system / shutdown_rss_system | 配置开关 | 启动/停止调度器 | 启动失败仅 warning，不阻断服务器 | P1 |
| FP10 | 内存清理 — 处理完 feed 后 del feed + gc.collect() | — | 释放内存 | — | P2 |

### 业务规则

| R# | 描述 | 校验方式 | 证据级别 |
|----|------|---------|---------|
| R1 | RSS 源最大 10MB，分两阶段检查：Content-Length 头 + 流式累积字节数 | `fetch_rss_feed()`:31,45,55 — 常量 MAX_RSS_SIZE = 10MB | A |
| R2 | Content-Length 头不可信时（缺失），以流式累积字节数为准 | 流式读取时 `if len(content) > MAX_RSS_SIZE` 检查（:55） | A |
| R3 | RSS 条目按 link 字段去重，已存在则保留原 key 和 createdTime | `_save_or_update_entry()`:98–107 | A |
| R4 | 批量解析 Semaphore 限制 3 并发，防止对外部源造成过大压力 | `RSSSchedulerManager._PARSE_CONCURRENCY = 3` (:23) | A |
| R5 | 间隔模式最小 60 秒，防止过于频繁的抓取 | `set_config()`:184 — `if interval < 60: raise ValueError` | A |
| R6 | 调度器配置变更后自动重启（stop + start）以应用新配置 | `set_config()`:217–219 | A |
| R7 | RSS 系统初始化失败不阻断服务器启动（降级策略） | `init_rss_system()`:315–319 — try/except + warning | A |
| R8 | feedparser 解析警告（bozo）不阻断流程，仅记录 warning | `fetch_rss_feed()`:63–64 | A |

### 数据约束

| 约束 | 类型 | 范围/格式 | 来源 |
|------|------|----------|------|
| url | string | 有效 HTTP/HTTPS URL | `parse_feed()`:152 |
| interval | int | ≥ 60 秒 | `set_config()`:184 |
| cron second | int | 0–59 | `set_config()`:198 |
| cron minute | int | 0–59 | `set_config()`:199 |
| cron hour | int | 0–23 | `set_config()`:200 |
| cron day | int | 1–31 | `set_config()`:201 |
| cron month | int | 1–12 | `set_config()`:202 |
| cron day_of_week | int | 0–6 | `set_config()`:203 |
| MAX_RSS_SIZE | int | 10,485,760 (10MB) | `fetch_rss_feed()`:31 |
| RSS_CHUNK_SIZE | int | 8192 (8KB) | `feed_service.py`:15 |
| PARSE_CONCURRENCY | int | 3 | `rss_scheduler.py`:23 |

---

## §3 成功标准

| SC# | 描述 | 度量方式 | 目标值 | 优先级 | 关联 FP# |
|-----|------|---------|--------|--------|---------|
| SC1 | 单个 RSS 源成功抓取并入库 | 提供有效 RSS URL → 调用 parse_feed → 检查 saved_count | saved_count + updated_count > 0 | P0 | FP1–FP3 |
| SC2 | 重复抓取不产生重复条目 | 两次抓取同一 RSS URL → 检查总条目数 | 条目数不增加（updated_count 可能增加） | P0 | FP3 |
| SC3 | 超过 10MB 的 RSS 源被拒绝 | 提供 Content-Length > 10MB 的 URL → 调用 fetch_rss_feed | BusinessException 抛出 | P0 | FP1 |
| SC4 | 批量解析时单个源失败不阻断其他 | 3 个源中 1 个 URL 无效 → 调用 parse_all_sources | success_count=2, failed_count=1 | P0 | FP4 |
| SC5 | 调度器间隔 < 60s 被拒绝 | set_config interval=30 | ValueError("定时器间隔不能小于 60 秒") | P1 | FP6 |
| SC6 | Cron 字段范围校验生效 | set_config cron second=99 | ValueError("second 必须在 0-59 之间") | P1 | FP7 |

---

## §4 范围边界

### 范围内

| # | 条目 | 关联 FP# | 边界说明 |
|---|------|---------|---------|
| 1 | RSS/Atom 源抓取与解析 | FP1, FP2 | HTTP GET + feedparser，10MB 限制 |
| 2 | Link 去重入库 | FP3 | 存在更新、不存在创建 |
| 3 | 定时调度管理 | FP6–FP9 | APScheduler 间隔/Cron 双模式 |
| 4 | 批量并发解析 | FP4, FP5 | Semaphore(3) + asyncio.gather |

### 范围外

| # | 条目 | 排除原因 | 替代方案 |
|---|------|---------|---------|
| 1 | RSS 源的增删改（CRUD） | 属于 data_service 层通过 seeds 集合管理 | `query_documents` / `create_document` 操作 seeds 集合 |
| 2 | RSS 内容全文检索 | 属于数据查询层 | `query_documents` 的模糊搜索能力 |
| 3 | 分布式调度 | 当前单进程部署 | 后续可引入 Celery/Redis |
| 4 | 非 RSS/Atom 格式的网页抓取 | feedparser 仅支持 RSS/Atom | 需要独立的网页抓取服务 |

---

## §5 AC

| AC# | Given | When | Then | 门禁 |
|-----|-------|------|------|------|
| AC1 | 提供有效 RSS URL | 调用 parse_feed(url=...) | 返回 success=true，saved_count 或 updated_count > 0 | Gate A |
| AC2 | RSS 集合中已有 link=X 的条目 | 再次抓取包含 link=X 的 RSS 源 | 原条目 key 和 createdTime 不变，其他字段更新 | Gate A |
| AC3 | RSS URL 返回 404 | 调用 fetch_rss_feed(url) | BusinessException(INVALID_PARAMS, "HTTP 状态码: 404") | Gate A |
| AC4 | RSS 源 Content-Length > 10MB | 调用 fetch_rss_feed(url) | BusinessException(INVALID_PARAMS, "RSS 源过大") | Gate A |
| AC5 | seeds 集合中有 3 个启用源 | 调用 parse_all_enabled_rss_sources | 返回 total_sources=3, results 含 3 个结果 | Gate A |
| AC6 | 调度器未运行 | 调用 start_rss_scheduler | 调度器启动，is_running=true | Gate A |
| AC7 | 调度器正在运行 | 调用 stop_rss_scheduler | 调度器停止，is_running=false | Gate A |
| AC8 | 提供 config type=interval, interval=7200 | 调用 set_scheduler_config(config) | 调度器以 7200s 间隔运行；get_status 返回 interval=7200 | Gate A |

---

## §6 风险与假设

| # | 风险/假设 | 类型 | 可能性 | 影响 | 缓解/验证策略 | 关联 FP# |
|---|----------|------|--------|------|-------------|---------|
| 1 | 外部 RSS 源不稳定（超时、断连、格式变化） | 风险 | H | M | 60s 超时 + aiohttp 异常捕获 + 单源失败不影响批量 | FP1, FP4 |
| 2 | 恶意 RSS 源返回超大内容耗尽内存 | 风险 | M | H | 双重检查（Content-Length + 流式累积），10MB 硬限制 | FP1 |
| 3 | RSS link 变化导致同一内容重复入库 | 风险 | M | M | 依赖 link 字段去重；若 RSS 源的 guid/isPermaLink 变化则无法去重 | FP3 |
| 4 | 定时任务在服务器重启后丢失 | 风险 | M | L | init_rss_system() 在启动时调用，自动恢复调度器 | FP9 |
| 5 | seeds 集合查询失败导致批量解析无法获取源列表 | 风险 | L | M | `_get_enabled_sources()` 异常时返回空列表，不阻断调度循环 | FP5 |
| 6 | RSS 源可正常访问且返回有效的 RSS/Atom 格式 | 假设 | — | — | 用户负责提供有效 RSS URL；格式错误时抛异常提示 | FP1 |
| 7 | feedparser 正确处理常见 RSS/Atom 变体 | 假设 | — | — | feedparser 是成熟库；bozo 警告不阻断 | FP2 |

---

### 主要价值

- 📡 **自动内容汇聚** — 从外部 RSS 源自动抓取内容，支持单次和批量模式
- 🔗 **智能去重入库** — 按 link 自动判断新增或更新，保留历史 key 和创建时间
- ⏱️ **灵活定时调度** — 间隔模式（≥60s）和 Cron 模式双支持，配置热更新无需重启
- 🛡️ **多层安全防护** — 10MB 大小双检查 + 60s 超时 + 流式分块读取防内存溢出
- 🔄 **并发控制** — Semaphore 限流 3 并发，防止对外部源造成过大压力

---

## 回溯链

| 来源 | 路径 | 证据级别 |
|------|------|---------|
| 源码 | `src/services/rss/feed_service.py` (175 lines) | A |
| 源码 | `src/services/rss/rss_scheduler.py` (331 lines) | A |
| 依赖 | `src/core/database.py` — db 单例 | B |
| 依赖 | `src/core/config.py` — collection_rss / collection_seeds / rss_scheduler_interval | B |

### 变更记录

| 日期 | 版本 | 变更内容 | 来源 |
|------|------|---------|------|
| 2026-05-22 | 1.0.0 | 初始文档基线，从源码反推生成 | /rui doc --from-code services-rss |
