# YiAi-测试设计 — services-rss

> RSS 订阅服务的测试设计文档。覆盖 `feed_service.py` 全部函数 + `rss_scheduler.py` 调度器管理。
>
> **来源**：源码分析 `/rui doc --from-code services-rss`
> **证据等级**：B（只读源码 + 静态分析）
> **项目类型**：backend
>
> **注意**：`fetch_rss_feed()` 和 `process_feed_from_url()` 依赖外部 HTTP 请求，测试时需 mock aiohttp 或使用本地测试 RSS 文件。

---

## 效果示意

```mermaid
flowchart LR
    STORY["故事任务 AC#"]:::story --> TC["测试用例"]:::test
    TC --> GATE_A["Gate A<br/>测试先行验证"]:::gate

    classDef story fill:#fff3e0,stroke:#e65100;
    classDef test fill:#e3f2fd,stroke:#1565c0;
    classDef gate fill:#e8f5e9,stroke:#2e7d32;
```

---

## 测试用例

### TC1: parse_feed — 有效 RSS URL 抓取

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP1, FP2, FP3 |
| 前置条件 | mock aiohttp 返回有效 RSS XML |
| 输入 | `parse_feed({url: 'http://test/rss', name: 'Test'})` |
| 预期 | success=true, saved_count ≥ 0, source='Test' |
| 验证点 | fetch → parse → save 管道完整执行 |

### TC2: parse_feed — 缺少 URL 参数

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP1 |
| 前置条件 | 无 |
| 输入 | `parse_feed({})` |
| 预期 | 抛出 ValueError("URL is required") |
| 验证点 | 参数校验在 HTTP 请求之前 |

### TC3: fetch_rss_feed — HTTP 404 响应

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC3 |
| 关联 FP# | FP1 |
| 前置条件 | mock aiohttp 返回 status=404 |
| 输入 | `fetch_rss_feed('http://test/404')` |
| 预期 | BusinessException(INVALID_PARAMS, "HTTP 状态码: 404") |
| 验证点 | 非 200 状态正确转换为业务异常 |

### TC4: fetch_rss_feed — Content-Length 超限

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC4 |
| 关联 FP# | FP1 |
| 前置条件 | mock aiohttp 返回 Content-Length: 11534336 (>10MB) |
| 输入 | `fetch_rss_feed('http://test/huge')` |
| 预期 | BusinessException(INVALID_PARAMS, "RSS 源过大") |
| 验证点 | Content-Length 预检生效 |

### TC5: fetch_rss_feed — 流式读取超限

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC4 |
| 关联 FP# | FP1 |
| 前置条件 | mock aiohttp 无 Content-Length 头，流式返回 11MB 数据 |
| 输入 | `fetch_rss_feed('http://test/huge-stream')` |
| 预期 | BusinessException(INVALID_PARAMS, "RSS 源实际内容过大") |
| 验证点 | 流式累积检查兜底 Content-Length 缺失情况 |

### TC6: fetch_rss_feed — 网络超时

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC3 |
| 关联 FP# | FP1 |
| 前置条件 | mock aiohttp 触发 asyncio.TimeoutError |
| 输入 | `fetch_rss_feed('http://test/timeout')` |
| 预期 | BusinessException 被抛出（通过 aiohttp.ClientError 分支） |
| 验证点 | 60s 超时配置 + 异常类型转换正确 |

### TC7: _save_or_update_entry — 新条目创建

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP3 |
| 前置条件 | mock collection，link 不存在 |
| 输入 | `_save_or_update_entry(collection, {link: 'http://new', title: 'New'}, '2026-01-01')` |
| 预期 | 返回 (1, 0)；insert_one 被调用；key 为 UUID v4 格式 |
| 验证点 | added=1, updated=0 |

### TC8: _save_or_update_entry — 已有条目更新

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC2 |
| 关联 FP# | FP3 |
| 前置条件 | mock collection 返回已有文档（含 key 和 createdTime） |
| 输入 | `_save_or_update_entry(collection, {link: 'http://exist', title: 'Updated'}, '2026-05-22')` |
| 预期 | 返回 (0, 1)；update_one 被调用；key 和 createdTime 保持原值 |
| 验证点 | added=0, updated=1（若 modified_count > 0） |

### TC9: process_feed_from_url — 完整管道

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1, AC2 |
| 关联 FP# | FP1–FP3, FP10 |
| 前置条件 | mock aiohttp 返回含 3 个 entry 的 RSS，其中 1 个 link 已存在 |
| 输入 | `process_feed_from_url('http://test/rss', 'TestSource')` |
| 预期 | success=true, saved_count=2, updated_count=1, total_items=3 |
| 验证点 | 去重逻辑正确；内存清理执行 |

### TC10: process_feed_from_url — entry 无 link 跳过

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP2, FP3 |
| 前置条件 | mock feed 含 3 个 entry，其中 1 个无 link 字段 |
| 输入 | `process_feed_from_url('http://test/rss')` |
| 预期 | total_items=2（无 link 的跳过） |
| 验证点 | `if not entry.get('link'): continue` 生效 |

### TC11: parse_all_enabled_rss_sources — 批量成功

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC5 |
| 关联 FP# | FP4, FP5 |
| 前置条件 | mock seeds 集合返回 3 个启用源；mock process_feed_from_url 全部成功 |
| 输入 | `parse_all_enabled_rss_sources()` |
| 预期 | total_sources=3, success_count=3, failed_count=0 |
| 验证点 | asyncio.gather 并发执行 |

### TC12: parse_all_enabled_rss_sources — 部分失败隔离

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC5 |
| 关联 FP# | FP4 |
| 前置条件 | mock 3 个源，其中 1 个 process 失败（返回 success=false） |
| 输入 | `parse_all_enabled_rss_sources()` |
| 预期 | total_sources=3, success_count=2, failed_count=1 |
| 验证点 | 单源失败不阻断其他源 |

### TC13: parse_all_enabled_rss_sources — 无启用源

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP5 |
| 前置条件 | mock seeds 集合返回空列表 |
| 输入 | `parse_all_enabled_rss_sources()` |
| 预期 | total_sources=0, success_count=0, results=[] |
| 验证点 | 优雅处理空源列表 |

### TC14: start_rss_scheduler — 正常启动

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC6 |
| 关联 FP# | FP6 |
| 前置条件 | 调度器未运行 |
| 输入 | `start_rss_scheduler()` |
| 预期 | scheduler._running = True |
| 验证点 | 调度器启动；间隔/Cron 模式按配置选择 |

### TC15: stop_rss_scheduler — 正常停止

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC7 |
| 关联 FP# | FP6 |
| 前置条件 | 调度器正在运行 |
| 输入 | `stop_rss_scheduler()` |
| 预期 | scheduler._running = False；_scheduler = None |
| 验证点 | shutdown 调用；实例置空 |

### TC16: start 重复调用 — 不报错

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC6 |
| 关联 FP# | FP6 |
| 前置条件 | 调度器已在运行 |
| 输入 | `start_rss_scheduler()` |
| 预期 | 仅记录 warning，不抛异常，状态保持运行 |
| 验证点 | `if self._running: logger.warning(...); return` |

### TC17: set_scheduler_config — 间隔模式

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC8 |
| 关联 FP# | FP6, FP8 |
| 前置条件 | 调度器正在运行（间隔=3600） |
| 输入 | `set_scheduler_config({type: 'interval', interval: 7200})` |
| 预期 | config.interval=7200；调度器已重启；get_status 返回 interval=7200 |
| 验证点 | 配置更新 + stop+start 热重启 |

### TC18: set_scheduler_config — 间隔 < 60 秒

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP6 |
| 前置条件 | 任意状态 |
| 输入 | `set_scheduler_config({type: 'interval', interval: 30})` |
| 预期 | ValueError("定时器间隔不能小于 60 秒") |
| 验证点 | 最小值校验 |

### TC19: set_scheduler_config — Cron 模式

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP7, FP8 |
| 前置条件 | 调度器正在运行 |
| 输入 | `set_scheduler_config({type: 'cron', cron: {hour: 8, minute: 0}})` |
| 预期 | config.type='cron'；调度器已重启；get_status 返回 cron 配置 |
| 验证点 | CronTrigger 创建正确；热重启 |

### TC20: set_scheduler_config — Cron 字段范围校验

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP7 |
| 前置条件 | 任意状态 |
| 输入 | `set_scheduler_config({type: 'cron', cron: {second: 99}})` |
| 预期 | ValueError("second 必须在 0-59 之间") |
| 验证点 | 各字段 range 校验生效 |

### TC21: get_scheduler_status_info — 状态查询

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP6, FP7 |
| 前置条件 | 调度器以 interval=3600 运行 |
| 输入 | `get_scheduler_status_info()` |
| 预期 | {enabled: true, type: 'interval', interval: 3600, cron: {...}} |
| 验证点 | 状态信息完整准确 |

### TC22: init_rss_system — 启动成功

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC6 |
| 关联 FP# | FP9 |
| 前置条件 | `is_rss_scheduler_enabled()` 返回 True |
| 输入 | `init_rss_system()` |
| 预期 | 调度器启动；is_running=True |
| 验证点 | 配置开关生效 |

### TC23: init_rss_system — 启动失败降级

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP9 |
| 前置条件 | `is_rss_scheduler_enabled()` 返回 True，start() 抛异常 |
| 输入 | `init_rss_system()` |
| 预期 | 记录 warning，不抛异常，不阻断调用方 |
| 验证点 | try/except 降级策略生效 |

### TC24: shutdown_rss_system — 正常关闭

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC7 |
| 关联 FP# | FP9 |
| 前置条件 | 调度器正在运行 |
| 输入 | `shutdown_rss_system()` |
| 预期 | 调度器停止；is_running=False |
| 验证点 | stop + 异常降级 |

---

## Gate A 交接信号

| 检查项 | 状态 | 说明 |
|--------|:---:|------|
| 测试用例覆盖全部 AC# | ✓ | AC1–AC8 均有 ≥1 TC 覆盖 |
| 测试用例覆盖全部公共函数 | ✓ | 7 个公共函数均有 TC |
| HTTP 异常场景覆盖 | ✓ | 404 / Content-Length 超限 / 流式超限 / 超时 |
| 去重逻辑测试 | ✓ | TC7（新建）/ TC8（更新）/ TC10（跳过无 link） |
| 批量并发测试 | ✓ | TC11（全成功）/ TC12（部分失败）/ TC13（空列表） |
| 调度器状态机测试 | ✓ | 启动/停止/重复调用/热配置更新 |
| 降级策略测试 | ✓ | TC23（init 失败）/ TC5（Content-Length 缺失兜底） |
| 参数校验测试 | ✓ | TC2（缺 URL）/ TC18（间隔 < 60）/ TC20（Cron 范围） |

---

### 主要价值

- ✅ **AC 全覆盖** — 24 个测试用例覆盖全部 8 个验收条件
- 🛡️ **安全场景充分** — 10MB 双阶段检查 + 超时 + 并发限流
- 🔄 **去重逻辑完整** — 新建/更新/跳过三种路径全覆盖
- ⏱️ **调度器状态机完备** — 启动/停止/重复调用/热重启/降级全覆盖

---

## 回溯链

| 来源 | 路径 | 证据级别 |
|------|------|---------|
| 故事任务 | `YiAi-故事任务.md` §5 AC1–AC8 | A |
| 使用场景 | `YiAi-使用场景.md` 场景 1–6 | A |
| 技术评审 | `YiAi-技术评审.md` §2 API 签名 | A |
| 源码 | `src/services/rss/feed_service.py` | A |
| 源码 | `src/services/rss/rss_scheduler.py` | A |

### 变更记录

| 日期 | 版本 | 变更内容 | 来源 |
|------|------|---------|------|
| 2026-05-22 | 1.0.0 | 初始文档基线，从源码反推生成 | /rui doc --from-code services-rss |
