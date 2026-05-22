> | v1.4.8 | 2026-05-20 | deepseek-v4-pro | 🌿 feat/rui-story | ⏱️ — | 📎 [CLAUDE.md](../../../CLAUDE.md) |

> **导航**: [YrY-使用场景 →](./YrY-使用场景.md)

> **来源引用**: 从 `skills/rui-story/` 源码反推生成，证据 Level B + 源码路径。`doc --from-code rui-story`

[§1 Story](#sec1-story) · [§2 Requirements](#sec2-requirements) · [§3 成功标准](#sec3-success) · [§4 范围边界](#sec4-scope) · [§5 AC](#sec5-ac) · [§6 风险与假设](#sec6-risks) · [§7 跨文档索引](#sec7-index) · [§L 自改进循环](#secL-improve)

---

### §0 基线声明

> **问题空间基线 (Problem Space Baseline)**: 本文档定义"做什么(WHAT)"和"为什么(WHY)"。所有后续文档(03-09)的设计、实现、验证、改进决策均必须可追溯至本文档的具体章节。

---

### 需求概述

为 YrY 故事驱动 SDLC 编排系统提供故事任务面板管理能力。用户可通过 `/rui-story` 命令族查询远端故事面板状态、查看单故事详情、从远端同步文档到本地、清理非项目文件。数据源默认为远端 API（api.effiy.cn），查询操作零本地文件系统读取，写入操作（sync/clear/remove）有明确的数据边界。

### 效果示意

```mermaid
flowchart TD
    NOW["当前状态<br/>故事面板查询依赖本地文件系统<br/>缺乏远端数据视图"]:::pain
    NOW --> M1["里程碑 1<br/>远端 API 查询引擎<br/>sessions → 故事分组"]:::milestone
    M1 --> M2["里程碑 2<br/>状态判定与类型推断<br/>6 状态 + 4 类型"]:::milestone
    M2 --> M3["里程碑 3<br/>只读命令族<br/>概览/list/show/recommend/health"]:::milestone
    M3 --> M4["里程碑 4<br/>写入命令族<br/>sync/clear/remove<br/>明确数据边界"]:::milestone
    M4 --> GOAL["目标状态<br/>故事面板管理完整可独立运作<br/>远端查询·本地清理·状态准确"]:::goal

    classDef pain fill:#ffebee,stroke:#c62828;
    classDef milestone fill:#fff3e0,stroke:#e65100;
    classDef goal fill:#e8f5e9,stroke:#2e7d32;
```

### 主要价值

- 🎯 统一故事面板查询入口 — 远端 API 为默认数据源，覆盖概览/列表/详情/推荐/健康检查
- 🔒 数据边界清晰 — 查询不读本地、写入有明确范围、clear/remove 仅操作本地文件系统
- ⚡ 确定性脚本执行 — recommend/health 由 rui-story.mjs 确定性输出，不依赖 agent 解读
- 📊 状态自动判定 — 基于远端 file_path 存在性自动判定 6 种故事状态，含 blocked 本地例外
- 🔀 与 rui 管线分离 — 面板管理独立于 SDLC 编排，list 命令从 rui 迁移至 rui-story

---

<a id="sec1-story"></a>

## §1 Story

### Story 1: 故事面板远端查询引擎

| 字段 | 内容 |
|------|------|
| 作为 | 项目参与者 |
| 我想要 | 通过统一入口查询远端故事任务面板的状态和进度 |
| 以便 | 无需查看本地文件系统即可了解所有故事的当前状态 |
| 优先级 | P0 |
| 范围边界 | 只读远端 API，不读本地文件系统，不改源码 |
| 依赖 | API_X_TOKEN 环境变量可用，远端 API 可达 |

#### 范围外

- 不涉及源码修改或 git 分支操作
- 不创建故事文档内容（那是 /rui doc 的职责）
- 不直接操作本地文件系统（查询操作）

##### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 状态概览 | 用户执行 `/rui-story` | 查询远端 API → 筛选故事任务面板 sessions → 按故事名分组 → 判定状态 → 聚合计数 | 输出状态统计 + 最近活动列表 |
| 2 | 进度全景 | 用户执行 `/rui-story list` | 查询远端 API → 逐故事判定状态 → 推断类型 → 检查 git 分支 | 输出所有故事的详细表格 |
| 3 | 单故事详情 | 用户执行 `/rui-story show <name>` | 查询远端 API → 筛选匹配故事 → 判定状态与类型 → 检查 git 分支 | 输出该故事的完整详述卡 |
| 4 | 同步推荐 | 用户执行 `/rui-story recommend` | 查询远端 API → 按故事名分组 → 统计文件数 | 输出可同步故事列表及推荐命令 |
| 5 | 健康检查 | 用户执行 `/rui-story health` | 读取项目名 → 检查 Token → 查询远端 API → 统计面板数据 | 输出系统诊断报告 |

---

### Story 2: 故事文档同步与本地清理

| 字段 | 内容 |
|------|------|
| 作为 | 项目维护者 |
| 我想要 | 从远端同步故事文档到本地，以及清理本地混入的非项目文件 |
| 以便 | 本地文档与远端保持一致，且仅保留当前项目的文档 |
| 优先级 | P0 |
| 范围边界 | sync 委托 import-docs，clear/remove 仅操作本地文件系统 |
| 依赖 | Story 1 完成，import-docs skill 可用 |

#### 范围外

- 不创建文档内容（那是 /rui doc 的职责）
- 不修改源码
- clear/remove 不触碰远端数据

##### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 同步故事文档 | 用户执行 `/rui-story sync <name>` | 委托 import-docs mode=pull → 从远端下载覆盖本地 | 本地文档与远端一致 |
| 2 | 同步推荐提示 | 用户执行 `/rui-story sync`（无参数） | 查询远端可同步故事 → 展示推荐列表 | 用户选择后执行定向同步 |
| 3 | 清理非项目文件 | 用户执行 `/rui-story clear [<name>]` | 读取 CLAUDE.md 项目前缀 → 扫描目录 → 展示删除/保留双重清单 → 确认后删除 | 仅保留 `{project}-` 前缀文件 |
| 4 | 删除故事目录 | 用户执行 `/rui-story remove <name>` | 检查目录存在 → 展示内容清单 → 确认后删除整个目录 | 本地目录完全删除，远端不受影响 |

---

### Story 3: 帮助系统与错误处理

| 字段 | 内容 |
|------|------|
| 作为 | 新用户 |
| 我想要 | 通过 `--help` 获得完整的使用指导和场景示例 |
| 以便 | 无需查阅 SKILL.md 即可上手使用 |
| 优先级 | P1 |
| 范围边界 | 只读，确定性输出 |
| 依赖 | help.mjs 脚本存在 |

##### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 查看帮助 | 用户执行 `/rui-story --help` | 执行 `node skills/rui-story/help.mjs` | 输出完整帮助含场景示例 |
| 2 | Token 缺失提示 | API_X_TOKEN 未配置时执行查询命令 | 检测 Token → 输出配置指引 | 提示配置方法后退出 |
| 3 | 远端不可达 | API 查询失败 | 捕获异常 → 输出错误信息 | 优雅退出，显示错误原因 |

---

<a id="sec2-requirements"></a>

## §2 Requirements

### 功能点

| FP# | 描述 | 输入 | 输出 | 错误行为 | 优先级 |
|-----|------|------|------|---------|--------|
| FP1 | 远端会话查询 — 查询 sessions 集合并筛选故事任务面板数据 | API URL + Token | 按故事分组的 session 列表 | API 不可达时优雅退出并提示 | P0 |
| FP2 | 故事状态判定 — 基于远端 file_path 存在性判定 6 种状态 | file_path 集合 + 项目前缀 + 本地 blocked 状态 | 状态标签 | 无法判定时默认为 not_started | P0 |
| FP3 | 项目类型推断 — 从远端技术评审内容推断前端/后端/全栈/元 | 技术评审文档内容 | 类型枚举 | 无法读取或解析时默认 meta | P1 |
| FP4 | 状态概览输出 — 按状态聚合计数 + 最近活动列表 | 故事状态映射 | 格式化概览文本 | 无数据时显示空状态提示 | P0 |
| FP5 | 进度全景表格 — 所有故事详情表格含状态/文件数/最后修改/类型/分支 | 故事状态映射 + 类型映射 | 格式化表格 | 无数据时显示空状态提示 | P0 |
| FP6 | 单故事详述卡 — 文件清单/状态/元数据/分支信息 | 故事名 + sessions | 格式化详述卡 | 故事不存在时列出已知故事名 | P0 |
| FP7 | 同步推荐列表 — 远端可同步故事及推荐命令 | 故事分组 | 推荐列表 + sync 命令 | 无数据时显示空状态提示 | P1 |
| FP8 | 健康检查报告 — 凭据/API 可达性/配置/数据完整性 | 环境变量 + 远端 API + 本地文件 | 诊断报告 | Token 缺失时跳过远端检查 | P1 |
| FP9 | 文档同步 — 委托 import-docs 从远端拉取文档到本地 | 故事名 | 同步完成的本地文档 | import-docs 失败时传递错误 | P0 |
| FP10 | 本地清理 — 仅保留 `{project}-` 前缀文件，其余删除 | 故事名(可选) + 项目前缀 | 清理后的目录 | 无匹配文件时不执行任何操作 | P0 |
| FP11 | 目录删除 — 删除整个故事本地目录 | 故事名(必填) | 已删除的目录 | 目录不存在时提示终止 | P1 |
| FP12 | 帮助输出 — 显示完整命令用法与场景示例 | — | 格式化帮助文本 | help.mjs 不存在时回退到内置帮助 | P1 |

### 业务规则

| R# | 描述 | 校验方式 | 证据级别 |
|----|------|---------|---------|
| R1 | 所有查询操作使用远端 API，不读本地文件系统 | 代码审查：overview/list/show/recommend 函数无 fs.readFileSync 调用 | B |
| R2 | 仅查询和同步故事面板状态，不创建文档内容 | 代码审查：无文件写入操作（除 sync/clear/remove） | B |
| R3 | 不修改源码，不创建/切换 git 分支 | 代码审查：无 Edit/Write 到 skills/agents/rules 目录 | B |
| R4 | sync 完全委托 import-docs | 代码审查：sync 调用 node skills/import-docs/sync.mjs | B |
| R5 | clear 仅操作本地文件系统，不触碰远端 | 代码审查：clear 逻辑无 fetch/网络请求 | B |
| R6 | clear 仅保留 `{project}-` 前缀文件，先展示后确认 | 用户交互流程验证 | B |
| R7 | remove 仅操作本地文件系统，name 必填，先展示后确认 | 用户交互流程验证 | B |
| R8 | recommend/health 由 rui-story.mjs 确定性执行 | 命令输出一致性验证 | B |

### 数据约束

| 约束 | 类型 | 范围/格式 | 来源 |
|------|------|----------|------|
| 故事名称 | string | `^[a-z0-9]+(-[a-z0-9]+)*$` (kebab-case) | 命名规范约定 |
| API URL | string | 有效 HTTPS URL，默认 `https://api.effiy.cn` | 环境变量 IMPORT_DOCS_API_URL |
| API Token | string | 非空字符串 | 环境变量 API_X_TOKEN |
| 项目前缀 | string | `{项目名}-`，从 CLAUDE.md 读取 | readProjectName() |
| 状态枚举 | enum | not_started / docs_in_progress / docs_done / code_in_progress / code_done / blocked | determineStatus() |
| 类型枚举 | enum | backend / frontend / fullstack / meta | inferType() |
| HTTP 超时 | number | 30,000ms | HTTP_TIMEOUT 常量 |
| 并发数 | number | 4 | CONCURRENCY 常量 |

---

<a id="sec3-success"></a>

## §3 成功标准

| SC# | 描述 | 度量方式 | 目标值 | 优先级 | 关联 FP# |
|-----|------|---------|--------|--------|---------|
| SC1 | 用户可在无参数情况下看到故事面板整体状态 | `/rui-story` 执行返回状态概览 | 6 种状态全部统计，最近活动正确排序 | P0 | FP1, FP2, FP4 |
| SC2 | 用户可看到所有故事的完整进度表格 | `/rui-story list` 执行返回进度全景 | 表格含 Story/Status/Files/Last Modified/Type/Branch 6 列 | P0 | FP1, FP2, FP3, FP5 |
| SC3 | 用户可查看任意故事的文件清单和元数据 | `/rui-story show <name>` 执行 | 文件清单完整，状态和类型准确 | P0 | FP1, FP2, FP3, FP6 |
| SC4 | 用户可从远端同步文档到本地 | `/rui-story sync <name>` 执行 | 本地文档与远端一致 | P0 | FP9 |
| SC5 | 用户可安全清理非项目文件，先看清单再确认 | `/rui-story clear <name>` 执行 | 仅保留 `{project}-` 文件，删除前展示双重清单 | P0 | FP10 |
| SC6 | 用户可通过健康检查了解系统状态 | `/rui-story health` 执行 | 覆盖凭据/API/配置/数据 4 个维度 | P1 | FP8 |
| SC7 | 用户可通过帮助系统快速上手 | `/rui-story --help` 执行 | 含命令表 + 场景示例 | P1 | FP12 |
| SC8 | Token 缺失时给出清晰指引而非报错 | 无 Token 执行查询命令 | 输出配置方法提示 | P0 | FP1 |

---

<a id="sec4-scope"></a>

## §4 范围边界

### 范围内

| # | 条目 | 关联 FP# | 边界说明 |
|---|------|---------|---------|
| 1 | 远端 API 查询引擎 | FP1 | 查询 sessions 集合，筛选故事任务面板数据 |
| 2 | 状态判定与类型推断 | FP2, FP3 | 基于远端数据自动判定，含本地 blocked 例外 |
| 3 | 只读命令族（概览/list/show/recommend/health） | FP4–FP8, FP12 | 零本地文件系统读取 |
| 4 | 文档同步（sync） | FP9 | 委托 import-docs，mode=pull |
| 5 | 本地清理（clear/remove） | FP10, FP11 | 仅操作本地文件系统，不触碰远端 |
| 6 | 帮助系统 | FP12 | help.mjs 确定性输出 |

### 范围外

| # | 条目 | 排除原因 | 替代方案 |
|---|------|---------|---------|
| 1 | 故事文档内容创建 | 那是 /rui doc 的职责 | 使用 `/rui doc <需求>` |
| 2 | 源码修改 | 那是 /rui code 的职责 | 使用 `/rui code <name>` |
| 3 | git 分支创建与切换 | 那是 /rui code 的职责 | git checkout -b feat/<name> |
| 4 | 远端文档删除 | 远端数据由 import-docs 管理 | — |
| 5 | 故事进度变更（如标记完成） | 那是 rui 管线的职责 | 管线末端自动更新状态 |

---

<a id="sec5-ac"></a>

## §5 AC

| AC# | Given | When | Then | 门禁 |
|-----|-------|------|------|------|
| AC1 | API_X_TOKEN 已配置，远端 API 可达 | 用户执行 `/rui-story` | 输出状态概览：6 种状态统计 + 最近活动 | Gate A |
| AC2 | API_X_TOKEN 已配置，远端有 ≥1 个故事 | 用户执行 `/rui-story list` | 输出进度全景表格，含 Story/Status/Files/Last Modified/Type/Branch | Gate A |
| AC3 | API_X_TOKEN 已配置，远端存在指定故事 | 用户执行 `/rui-story show <name>` | 输出详述卡：文件清单/类型/分支/元数据 | Gate A |
| AC4 | API_X_TOKEN 未配置 | 用户执行任意查询命令 | 输出 Token 缺失提示 + 配置方法 | Gate A |
| AC5 | 远端 API 不可达 | 用户执行任意查询命令 | 输出错误信息后优雅退出 | Gate A |
| AC6 | 用户指定故事名 | 用户执行 `/rui-story sync <name>` | 委托 import-docs 执行 mode=pull 同步 | Gate A |
| AC7 | 用户未指定故事名 | 用户执行 `/rui-story sync` | 展示可同步故事推荐列表 | Gate A |
| AC8 | 本地故事目录含非项目文件 | 用户执行 `/rui-story clear <name>` 并确认 | 删除非 `{project}-` 文件，保留项目文件 | Gate A |
| AC9 | 用户指定故事名 | 用户执行 `/rui-story remove <name>` 并确认 | 删除整个本地故事目录 | Gate A |
| AC10 | 用户需要帮助 | 用户执行 `/rui-story --help` | 输出完整帮助含场景示例 | Gate A |
| AC11 | 远端有可同步故事 | 用户执行 `/rui-story recommend` | 输出故事列表 + 推荐 sync 命令 | Gate A |
| AC12 | 系统环境正常 | 用户执行 `/rui-story health` | 输出含凭据/API/配置/数据 4 维度的诊断报告 | Gate A |

---

<a id="sec6-risks"></a>

## §6 风险与假设

| # | 风险/假设 | 类型 | 可能性 | 影响 | 缓解/验证策略 | 关联 FP# |
|---|----------|------|--------|------|-------------|---------|
| 1 | 远端 API 不可达导致所有查询命令失败 | 风险 | M | H | 优雅错误处理，输出明确错误信息；health 命令可提前检测 | FP1 |
| 2 | API_X_TOKEN 未配置导致新用户无法使用 | 风险 | H | M | 检测缺失时输出配置指引而非报错 | FP1 |
| 3 | 远端 sessions 数据量大导致查询性能下降 | 风险 | M | M | limit=10000，并发类型推断（4 worker） | FP1, FP3 |
| 4 | 项目名解析失败导致状态判定错误 | 风险 | L | H | readProjectName() 多模式回退 + 目录名 fallback | FP2 |
| 5 | clear 误删重要文件 | 风险 | M | H | 双重清单展示 + 用户确认机制 + 仅操作本地 | FP10 |
| 6 | 类型推断依赖远端文件内容读取，网络延迟影响 list 命令响应时间 | 风险 | M | L | 并发读取（CONCURRENCY=4），失败默认 meta | FP3 |
| 7 | 远端 API 响应格式变更导致解析失败 | 风险 | L | H | 防御性解析 `data?.data?.list \|\| data?.list \|\| []` | FP1 |
| 8 | help.mjs 不存在时回退机制不工作 | 风险 | L | L | fallbackHelp() 内置最小帮助 | FP12 |
| 9 | API_X_TOKEN 始终可用 | 假设 | — | — | health 命令可验证凭据状态 | FP1 |
| 10 | 远端 sessions 的 file_path 以 `故事任务面板/` 为前缀 | 假设 | — | — | groupSessionsByStory 按此前缀筛选 | FP1 |
| 11 | CLAUDE.md 项目名可被确定性解析 | 假设 | — | — | 3 种解析模式 + fallback | FP2 |

---

<a id="sec7-index"></a>

## §7 跨文档索引

| 本文档章节 | 基线内容 | 下游文档编号 | 预期覆盖 |
|-----------|---------|------------|---------|
| §1 Story 1 | 远端查询引擎需求 | 技术评审 §1 §2 | 架构设计 + API 接口 |
| §1 Story 2 | 同步与清理需求 | 技术评审 §1 §3 | 架构设计 + 数据模型 |
| §2 FP1–FP3 | 查询/状态/类型功能点 | 技术评审 §1 §2 | 系统架构 + API 接口 |
| §2 FP9–FP11 | 同步/清理/删除功能点 | 测试设计 §2 | 测试用例覆盖 |
| §2 R1–R8 | 业务规则 | 安全审计 §5 | 合规检查 |
| §5 AC1–AC12 | 验收标准 | 测试设计 §0 §2 | 测试用例逐一覆盖 |
| §6 风险 1–8 | 风险项 | 安全审计 §2 | 威胁建模覆盖 |

---

<a id="secL-improve"></a>

## §L 自改进循环

> 首次管线执行后通过 `/rui update` 追加，详见 [YrY-自改进复盘](./YrY-自改进复盘.md)。

---

> **变更记录**
>
> | 日期 | 变更 | 触发 | 证据 |
> |------|------|------|------|
> | 2026-05-20 | 初始生成 | doc --from-code rui-story | skills/rui-story/SKILL.md + rui-story.mjs |
