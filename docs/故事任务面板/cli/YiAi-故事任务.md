# YiAi-故事任务 — cli

> CLI 命令行工具故事任务。覆盖状态查询 CLI (state_query) 1 个组件。
>
> **来源**：源码分析 `/rui doc --from-code cli`
> **证据等级**：B（只读源码 + 静态分析）
> **项目类型**：backend

---

## 效果示意

```mermaid
flowchart LR
    NOW["当前状态<br/>CLI 工具无文档"]:::pain
    NOW --> GOAL["目标状态<br/>4 命令状态查询 CLI 清晰"]:::goal

    classDef pain fill:#ffebee,stroke:#c62828;
    classDef goal fill:#e8f5e9,stroke:#2e7d32;
```

---

## §1 Story

### Story 1: 状态查询 CLI（state_query）

| 字段 | 内容 |
|------|------|
| 作为 | 运维人员/开发者 |
| 我想要 | 通过命令行查询和导出系统中的状态记录 |
| 以便 | 无需调用 API 即可快速排查和导出数据 |
| 优先级 | P2 |
| 范围边界 | typer CLI，4 命令（list/get/export/stats），调用 StateStoreService |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 列表查询 | 用户执行 `list` 命令 | 解析过滤参数 → 调用 StateStoreService.query → 格式化输出（table/json/csv） | 终端显示结果或写入文件 |
| 2 | 单条详情 | 用户执行 `get <key>` | 调用 StateStoreService.get → JSON 打印 | 终端显示记录或 "Record not found" |
| 3 | 数据导出 | 用户执行 `export` 命令 | 委托 list 命令，page_size=8000 → 输出到文件 | 文件写入确认 |
| 4 | 统计概览 | 用户执行 `stats` 命令 | 查询 page_size=1 仅取 total → 显示总数 | 终端显示记录总数 |

---

## §2 Requirements

### 功能点

| FP# | 描述 | 命令 | 优先级 |
|-----|------|------|:---:|
| FP1 | 条件查询 — record_type/tags/title_contains/分页 | list | P1 |
| FP2 | 多格式输出 — table (rich) / json / csv | list | P1 |
| FP3 | 输出到文件 — --output 参数 | list | P2 |
| FP4 | 单条查询 — 按 key 精确获取 | get | P1 |
| FP5 | 批量导出 — 委托 list + page_size=8000 + 强制文件输出 | export | P2 |
| FP6 | 统计概览 — 查询总数不取详情 | stats | P2 |

### 业务规则

| R# | 描述 | 证据级别 |
|----|------|:---:|
| R1 | list 命令默认 table 格式，page_size=20 | A |
| R2 | export 命令强制 page_size=8000 + 输出到文件 | A |
| R3 | stats 命令用 page_size=1 仅获取 total | A |
| R4 | get 命令找不到记录时 exit(1) | A |
| R5 | sys.path.insert(0, "/var/www/YiAi/src") 硬编码路径 | A |

---

## §3 成功标准

| SC# | 描述 | 优先级 |
|-----|------|:---:|
| SC1 | list 命令返回终端表格显示记录列表 | P1 |
| SC2 | list --format json 输出合法 JSON | P1 |
| SC3 | get 不存在的 key 输出红色错误并 exit(1) | P1 |
| SC4 | stats 正确显示记录总数 | P2 |

---

## §4 范围边界

**范围内**：state_query.py 4 命令
**范围外**：其他 CLI 工具、数据库直连操作

---

## §5 AC

| AC# | Given | When | Then | 门禁 |
|-----|-------|------|------|------|
| AC1 | state_records 含多条记录 | `python state_query.py list` | 终端表格显示记录 + 分页信息 | Gate A |
| AC2 | key 不存在 | `python state_query.py get nonexistent` | 红色 "Record not found" + exit 1 | Gate A |
| AC3 | 指定 --format json --output out.json | `python state_query.py list ...` | out.json 文件含合法 JSON | Gate A |
| AC4 | 无过滤条件 | `python state_query.py stats` | 正确显示 Total records 数量 | Gate A |

---

### 主要价值

- 📊 **终端查询** — 4 命令覆盖查询/详情/导出/统计
- 🎨 **多格式输出** — table (rich 表格) / json / csv 三种格式
- 📁 **文件导出** — list 和 export 支持 --output 写入文件
- 🔍 **条件过滤** — 支持 record_type/tags/title 多维度筛选

---

## 回溯链

| 来源 | 路径 | 证据级别 |
|------|------|---------|
| 源码 | `src/cli/state_query.py` (132 行) | A |
| 依赖 | `src/services/state/state_service.py` — StateStoreService | A |

### 变更记录

| 日期 | 版本 | 变更内容 | 来源 |
|------|------|---------|------|
| 2026-05-22 | 1.0.0 | 初始文档基线 | /rui doc --from-code cli |
