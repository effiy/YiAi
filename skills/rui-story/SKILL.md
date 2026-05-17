---
name: rui-story
description: Story panel CRUD and sync management. Manage stories under docs/故事任务面板/. Command: /rui-story.
user_invocable: true
lifecycle: default-pipeline
---

# rui-story

> 故事任务面板管理：增 · 删 · 改 · 查 · 同步。操作边界仅限 `docs/故事任务面板/`。
>
> **--help / -h**：执行 `node skills/rui-story/help.mjs` 输出完整帮助（含场景示例）。用户输入 `/rui-story --help` 或 `/rui-story -h` 或 `/rui-story help` 时，跳过管线逻辑，直接运行脚本并将输出展示给用户。
>
> 哲学源自 [CLAUDE.md](../../CLAUDE.md)。本文件定义命令面与操作规约。

## 命令族全景

```mermaid
flowchart TD
    ENTRY["/rui-story"]:::entry --> Q1{"有参数吗?"}
    Q1 -->|"无"| OVERVIEW["状态概览<br/>按状态统计 + 最近活动"]:::read
    Q1 -->|"有"| Q2{"哪个子命令?"}
    Q2 -->|"list"| LIST["进度全景<br/>所有故事详细表格"]:::read
    Q2 -->|"show &lt;name&gt;"| SHOW["单故事详情<br/>文件清单/状态/元数据"]:::read
    Q2 -->|"create &lt;name&gt;"| CREATE["创建故事目录<br/>仅目录骨架 .memory/"]:::write
    Q2 -->|"delete &lt;name&gt;"| DELETE["删除故事目录<br/>需用户确认"]:::write
    Q2 -->|"sync &lt;name&gt;?"| SYNC["文档同步<br/>委托 import-docs"]:::write
    Q2 -->|"rename &lt;old&gt; &lt;new&gt;"| RENAME["重命名故事目录<br/>警告 git 分支"]:::write

    classDef entry fill:#fff3e0,stroke:#e65100;
    classDef read fill:#e8f5e9,stroke:#2e7d32;
    classDef write fill:#e3f2fd,stroke:#1565c0;
```

| 命令 | 类型 | 作用 |
|------|------|------|
| `/rui-story` | 只读 | 状态概览：按状态统计 + 最近活动 |
| `/rui-story list` | 只读 | 进度全景：所有故事详细表格（状态/文件数/最后修改/分支） |
| `/rui-story show <Project>-<name>` | 只读 | 单故事详情：文件清单/状态/元数据/git 分支 |
| `/rui-story create <Project>-<name> [--type]` | 写入 | 创建故事目录骨架（仅目录 + `.memory/`），不含文档 |
| `/rui-story delete <Project>-<name>` | 写入 | 删除故事目录（需用户确认，警告 git 分支） |
| `/rui-story sync [<Project>-<name>]` | 写入 | 触发 import-docs 同步，限一个故事或全量 |
| `/rui-story rename <old> <new>` | 写入 | 重命名故事目录（警告 git 分支） |

`<Project>-<name>`：`<Project>` = PascalCase，`<name>` = kebab-case。如 `YiWeb-user-login`。

## 操作边界

```mermaid
flowchart LR
    subgraph 允许["✅ 允许"]
        A1["docs/故事任务面板/<br/>目录结构管理"]:::ok
        A2["import-docs 同步委托"]:::ok
    end
    subgraph 禁止["❌ 禁止"]
        B1["创建故事文档内容<br/>那是 /rui doc"]:::bad
        B2["修改源码<br/>那是 /rui code"]:::bad
        B3["创建/切换 git 分支<br/>那是 /rui code"]:::bad
    end

    classDef ok fill:#e8f5e9,stroke:#2e7d32;
    classDef bad fill:#ffebee,stroke:#c62828;
```

## 状态判定

> 按文件存在性 + `.memory/rui-state.json` 判定故事状态。

```mermaid
flowchart TD
    START["扫描故事目录"]:::s --> CHK01{"01-故事任务.md<br/>存在?"}
    CHK01 -->|"否"| NS["not_started"]:::s0
    CHK01 -->|"是"| CHKDOC{"文档基线齐全?<br/>含 02 05 + 按类型 03/04"}
    CHKDOC -->|"否"| DIP["docs_in_progress"]:::s1
    CHKDOC -->|"是"| CHKIMP{"实施报告存在?<br/>06 或 07"}
    CHKIMP -->|"否"| DD["docs_done"]:::s2
    CHKIMP -->|"是"| CHKVER{"08-测试用例报告.md<br/>存在?"}
    CHKVER -->|"否"| CIP["code_in_progress"]:::s3
    CHKVER -->|"是"| CHKBLK{"rui-state.json<br/>blocked=true?"}
    CHKBLK -->|"是"| BLK["blocked"]:::s5
    CHKBLK -->|"否"| CD["code_done"]:::s4

    classDef s fill:#e3f2fd,stroke:#1565c0;
    classDef s0 fill:#eceff1,stroke:#90a4ae;
    classDef s1 fill:#fff3e0,stroke:#e65100;
    classDef s2 fill:#e8f5e9,stroke:#2e7d32;
    classDef s3 fill:#e3f2fd,stroke:#1565c0;
    classDef s4 fill:#c8e6c9,stroke:#388e3c;
    classDef s5 fill:#ffebee,stroke:#c62828;
```

| 状态 | 条件 | 含义 |
|------|------|------|
| `not_started` | 01-故事任务.md 不存在 | 目录空或仅有元数据 |
| `docs_in_progress` | 01 存在，文档基线不完整 | 文档生成进行中 |
| `docs_done` | 文档基线齐全，实施报告不存在 | 等待编码 |
| `code_in_progress` | 06 或 07 存在，08 不存在 | 实现验证中 |
| `code_done` | 08 存在，未阻断 | 可交付 |
| `blocked` | `.memory/rui-state.json` 含 `blocked=true` | 管线阻断 |

项目类型按存在文件推断：有 03/06 = 含后端；有 04/07 = 含前端；两者均有 = fullstack；均无 = meta。

## `/rui-story` — 状态概览

> 无参数入口。扫描全部故事，按状态聚合，输出摘要 + 最近活动。

```mermaid
flowchart LR
    A["扫描<br/>docs/故事任务面板/"]:::op --> B["逐目录判定状态"]:::op
    B --> C["按状态聚合计数"]:::op
    C --> D["输出摘要表<br/>+ 最近修改的 5 个故事"]:::out

    classDef op fill:#e3f2fd,stroke:#1565c0;
    classDef out fill:#e8f5e9,stroke:#2e7d32;
```

**输出**：

```
故事任务面板 · 状态概览
─────────────────────────────
  code_done        0
  code_in_progress  0
  docs_done         0
  docs_in_progress  0
  not_started       0
  blocked           0
─────────────────────────────
  合计             0 个故事

最近活动：无
```

## `/rui-story list` — 进度全景

> 从 `/rui list` 迁移。扫描全部故事输出详情表格。

```mermaid
flowchart LR
    A["扫描<br/>docs/故事任务面板/"]:::op --> B["逐目录：状态 + 文件数<br/>+ 最后修改 + git 分支"]:::op
    B --> C["按最后修改降序排列"]:::op
    C --> D["输出表格"]:::out

    classDef op fill:#e3f2fd,stroke:#1565c0;
    classDef out fill:#e8f5e9,stroke:#2e7d32;
```

**输出列**：`Project | Story | Status | Files | Last Modified | Type | Branch`

- **Files**：故事目录下 `.md` 文件数量
- **Last Modified**：目录中最晚文件修改时间
- **Type**：按存在文件推断（backend / frontend / fullstack / meta）
- **Branch**：`git branch --list "feat/<Project>-<name>"` — 有则显示分支名，无则为 `—`

## `/rui-story show <Project>-<name>` — 单故事详情

```mermaid
flowchart LR
    PARSE["解析<br/>Project + name"]:::op --> LOCATE["定位目录<br/>docs/故事任务面板/&lt;P&gt;/&lt;n&gt;/"]:::op
    LOCATE --> ENUM["枚举文件<br/>含大小 / 修改时间"]:::op
    ENUM --> META["读取元数据<br/>.memory/rui-state.json<br/>story-type.json"]:::op
    META --> BRANCH["检查 git 分支<br/>git branch --list"]:::op
    BRANCH --> OUT["输出详述卡"]:::out

    classDef op fill:#e3f2fd,stroke:#1565c0;
    classDef out fill:#e8f5e9,stroke:#2e7d32;
```

**输出结构**：

```
<Project>-<name> · <status badge>

📂 目录: docs/故事任务面板/<Project>/<name>/
📋 类型: <type>
📄 文件: <N> 个

  文件清单:
  01-故事任务.md         2.3 KB  2026-05-17 10:30
  02-用户使用场景.md      4.1 KB  2026-05-17 10:35
  ...

🔀 Git 分支: feat/<Project>-<name>  (或 —)

📊 元数据:
  状态: <status>
  阶段: <current_stage>
  阻断原因: <block_reason 或 —>
```

## `/rui-story create <Project>-<name> [--type]` — 创建故事

```mermaid
flowchart TD
    PARSE["解析 &lt;Project&gt;-&lt;name&gt;"]:::op --> VALID{"格式校验<br/>PascalCase + kebab-case?"}
    VALID -->|"否"| ERR1["报错退出"]:::bad
    VALID -->|"是"| CONFLICT{"目标目录<br/>已存在?"}
    CONFLICT -->|"是"| ERR2["拒绝覆盖<br/>引导 /rui update"]:::bad
    CONFLICT -->|"否"| CREATE["创建目录<br/>docs/故事任务面板/&lt;P&gt;/&lt;n&gt;/"]:::op
    CREATE --> MEMORY["创建 .memory/<br/>写入 story-type.json"]:::op
    MEMORY --> DONE["输出创建确认"]:::out

    classDef op fill:#e3f2fd,stroke:#1565c0;
    classDef out fill:#e8f5e9,stroke:#2e7d32;
    classDef bad fill:#ffebee,stroke:#c62828;
```

- `--type`：`frontend` / `backend` / `fullstack` / `meta`（默认 `meta`）
- 仅创建目录 + `.memory/story-type.json`，**不创建任何文档**（文档由 `/rui doc` 生成）
- 目录已存在 → 拒绝覆盖，建议 `/rui update <name>`
- 写入 `.memory/story-type.json`：`{"type":"<type>","createdAt":"<ISO timestamp>"}`

## `/rui-story delete <Project>-<name>` — 删除故事

```mermaid
flowchart TD
    PARSE["解析名称"]:::op --> EXIST{"目录存在?"}
    EXIST -->|"否"| ERR["报错：不存在"]:::bad
    EXIST -->|"是"| BRANCH["检查 git 分支<br/>git branch --list"]:::op
    BRANCH --> WARN{"分支存在?"}
    WARN -->|"是"| WARNMSG["⚠ 警告：分支仍保留"]:::warn
    WARN -->|"否"| CONF
    WARNMSG --> CONF["请求用户确认<br/>输入 yes/no"]:::user
    CONF -->|"yes"| DEL["rm -rf 目录"]:::op
    CONF -->|"no"| CANCEL["取消"]:::out
    DEL --> CLEAN["清理空 Project 目录"]:::op
    CLEAN --> DONE["输出删除确认"]:::out

    classDef op fill:#e3f2fd,stroke:#1565c0;
    classDef out fill:#e8f5e9,stroke:#2e7d32;
    classDef bad fill:#ffebee,stroke:#c62828;
    classDef warn fill:#fff3e0,stroke:#e65100;
    classDef user fill:#f3e5f5,stroke:#6a1b9a;
```

- **必须用户确认**（输入 `yes`），不默认执行
- Git 分支**不删除**，仅警告
- 删除后若 Project 目录为空，一并清理

## `/rui-story sync [<Project>-<name>]` — 文档同步

```mermaid
flowchart LR
    Q{"有 &lt;name&gt;?"} -->|"是"| SCOPED["node skills/import-docs/sync.mjs<br/>dir=docs/故事任务面板/&lt;P&gt;/&lt;n&gt;/"]:::op
    Q -->|"否"| ALL["node skills/import-docs/sync.mjs<br/>dir=docs/故事任务面板/"]:::op
    SCOPED --> OUT["输出同步结果"]:::out
    ALL --> OUT

    classDef op fill:#e3f2fd,stroke:#1565c0;
    classDef out fill:#e8f5e9,stroke:#2e7d32;
```

- 完全委托 import-docs，不自行实现同步逻辑
- 限一个故事：`dir=docs/故事任务面板/<Project>/<name>/`
- 全量：`dir=docs/故事任务面板/`

## `/rui-story rename <old> <new>` — 重命名故事

```mermaid
flowchart TD
    PARSE["解析 old + new"]:::op --> VALID{"格式均有效?"}
    VALID -->|"否"| ERR1["报错退出"]:::bad
    VALID -->|"是"| EXIST{"old 目录存在?"}
    EXIST -->|"否"| ERR2["报错：不存在"]:::bad
    EXIST -->|"是"| CONFLICT{"new 目录<br/>已存在?"}
    CONFLICT -->|"是"| ERR3["拒绝覆盖"]:::bad
    CONFLICT -->|"否"| BRANCH["检查 git 分支"]:::op
    BRANCH --> WARN{"old 分支存在?"}
    WARN -->|"是"| WARNMSG["⚠ 分支需手动重命名"]:::warn
    WARN -->|"否"| MV
    WARNMSG --> MV["mv old new"]:::op
    MV --> CLEAN["清理空 Project 目录"]:::op
    CLEAN --> DONE["输出重命名确认"]:::out

    classDef op fill:#e3f2fd,stroke:#1565c0;
    classDef out fill:#e8f5e9,stroke:#2e7d32;
    classDef bad fill:#ffebee,stroke:#c62828;
    classDef warn fill:#fff3e0,stroke:#e65100;
```

- old 和 new 均为 `<Project>-<name>` 格式
- 仅重命名目录，不操作 git 分支
- 同名不操作

## 核心规则

```mermaid
flowchart LR
    subgraph 规则["6 条硬约束"]
        R1["仅管理目录结构<br/>不创建文档内容"]:::rule
        R2["不修改源码<br/>不创建/切换 git 分支"]:::rule
        R3["delete 必须用户确认"]:::rule
        R4["create 仅建目录骨架<br/>不与 /rui doc 竞争"]:::rule
        R5["sync 完全委托<br/>import-docs"]:::rule
        R6["PascalCase + kebab-case<br/>命名硬规范"]:::rule
    end

    classDef rule fill:#e3f2fd,stroke:#1565c0;
```

| # | 规则 | 违反处置 |
|---|------|---------|
| 1 | 只管理故事面板目录结构，不创建故事文档内容（那是 `/rui doc`） | 撤销误创建的文件 |
| 2 | 不修改源码，不创建/切换 git 分支（那是 `/rui code`） | — |
| 3 | delete 必须用户明确确认（输入 `yes`），不默认执行 | 补确认或取消 |
| 4 | create 只建目录骨架，不产出 01–10 文档 | 删除误创建的文档 |
| 5 | sync 完全委托 import-docs，不自行实现同步 | 修正命令重试 |
| 6 | `<Project>` = PascalCase，`<name>` = kebab-case | 拒绝执行 |

## 生效标志

```mermaid
flowchart LR
    F1["create 仅目录<br/>无文档文件"]:::sig --> F2["delete 前已确认<br/>git 分支已警告"]:::sig
    F2 --> F3["sync 正确委托<br/>import-docs"]:::sig
    F3 --> F4["rename 后新目录存在<br/>旧目录不存在"]:::sig
    F4 --> F5["list/show 状态<br/>判定准确"]:::sig

    classDef sig fill:#e8f5e9,stroke:#2e7d32;
```

| 标志 | 未达标的处置 |
|------|------------|
| create 仅建目录，无文档文件 | 删除误创建的文件 |
| delete 前已确认 + git 分支已警告 | 补确认、补警告 |
| sync 正确委托 import-docs | 修正命令参数重试 |
| rename 后新目录存在、旧目录不存在 | 手动修正 |
| list/show 状态判定准确 | 修正判定逻辑 |

## 与 rui 的关系

> rui-story 从 rui 接管了 `list` 命令。其余所有管线阶段（doc / code / update）仍由 rui 编排。

```mermaid
flowchart LR
    RUI["/rui<br/>SDLC 编排"]:::rui -->|"doc 创建文档"| PANEL["docs/故事任务面板/"]:::panel
    RS["/rui-story<br/>面板管理"]:::story -->|"CRUD + 同步"| PANEL

    classDef rui fill:#fff3e0,stroke:#e65100;
    classDef story fill:#e3f2fd,stroke:#1565c0;
    classDef panel fill:#e8f5e9,stroke:#2e7d32;
```
