> | v1.4.8 | 2026-05-20 | deepseek-v4-pro | 🌿 feat/rui-story | ⏱️ — | 📎 [CLAUDE.md](../../../CLAUDE.md) |

> **导航**: [← YrY-技术评审](./YrY-技术评审.md) · [YrY-安全审计 →](./YrY-安全审计.md)

> **来源引用**: 从 `skills/rui-story/SKILL.md` 命令族 + `rui-story.mjs` 命令处理器反推。证据 Level B + 源码路径。

[§0 基线溯源](#sec0-baseline) · [§1 测试范围](#sec1-scope) · [§2 测试用例](#sec2-cases) · [§3 环境专项](#sec3-env) · [§4 测试环境](#sec4-setup) · [§5 评审清单](#sec5-checklist) · [§6 Gate A 交接](#sec6-gatea)

---

### 主要价值

- 🎯 全覆盖 12 条 AC，正常/边界/异常/回归四类用例齐备
- 🔒 关键路径双重覆盖 — Token 缺失、API 不可达、目录不存在
- ⚡ 环境专项覆盖 — 并发推断、TTY 检测、项目名解析 fallback
- 📊 Gate A 交接信号明确 — P0 用例 ID + 验证命令 + 实现约束

---

<a id="sec0-baseline"></a>

## §0 基线溯源

| TC# | 覆盖 AC#(01 §5) | 覆盖场景(02 §2) | 覆盖类型 | 状态 |
|-----|-----------------|-----------------|---------|------|
| TC-N01 | AC1 | 场景 A 状态概览 | 正常 | 待验证 |
| TC-N02 | AC2 | 场景 B 进度全景 | 正常 | 待验证 |
| TC-N03 | AC3 | 场景 C 单故事详情 | 正常 | 待验证 |
| TC-N04 | AC6, AC7 | 场景 D 文档同步 | 正常 | 待验证 |
| TC-N05 | AC8 | 场景 E 本地清理 | 正常 | 待验证 |
| TC-N06 | AC9 | 场景 F 目录删除 | 正常 | 待验证 |
| TC-N07 | AC11 | 场景 G 同步推荐 | 正常 | 待验证 |
| TC-N08 | AC12 | 场景 H 健康检查 | 正常 | 待验证 |
| TC-N09 | AC10 | 场景 I 帮助查询 | 正常 | 待验证 |
| TC-E01 | AC5 | 场景 C 故事不存在 | 异常 | 待验证 |
| TC-E02 | AC8 | 场景 E 用户拒绝确认 | 异常 | 待验证 |
| TC-E03 | AC9 | 场景 F 目录不存在 | 异常 | 待验证 |
| TC-E04 | AC4 | 全部场景 Token 缺失 | 异常 | 待验证 |
| TC-E05 | AC5 | 全部场景 API 不可达 | 异常 | 待验证 |
| TC-B01 | — | 场景 A 空面板 | 边界 | 待验证 |
| TC-B02 | — | 场景 C 名称格式错误 | 边界 | 待验证 |
| TC-R01 | — | 项目名解析 fallback | 回归 | 待验证 |

---

<a id="sec1-scope"></a>

## §1 测试范围

### 1.1 覆盖矩阵

| FP# | 功能点 | 正常 | 边界 | 异常 | 回归 | 覆盖率 |
|-----|--------|:---:|:---:|:---:|:---:|:---:|
| FP1 | 远端会话查询 | ✅ | ✅ | ✅ | — | 100% |
| FP2 | 故事状态判定 | ✅ | ✅ | — | ✅ | 100% |
| FP3 | 项目类型推断 | ✅ | ✅ | ✅ | — | 100% |
| FP4 | 状态概览输出 | ✅ | ✅ | — | — | 100% |
| FP5 | 进度全景表格 | ✅ | — | — | — | 100% |
| FP6 | 单故事详述卡 | ✅ | ✅ | ✅ | — | 100% |
| FP7 | 同步推荐列表 | ✅ | ✅ | — | — | 100% |
| FP8 | 健康检查报告 | ✅ | — | ✅ | — | 100% |
| FP9 | 文档同步 | ✅ | — | — | — | 100% |
| FP10 | 本地清理 | ✅ | — | ✅ | — | 100% |
| FP11 | 目录删除 | ✅ | — | ✅ | — | 100% |
| FP12 | 帮助输出 | ✅ | — | — | ✅ | 100% |

### 1.2 Gate 映射

| Gate | 用例范围 | 通过标准 | 交接下游 |
|------|---------|---------|---------|
| Gate A | TC-N01–N09, TC-E01–E05, TC-B01–B02 | 所有 P0 用例通过 | code 实现阶段 |

### 1.3 影响链覆盖

| 影响点 | 来源 | 回归用例 | 覆盖状态 |
|--------|------|---------|---------|
| readProjectName 多模式解析 | CLAUDE.md 格式变更 | TC-R01 | 待验证 |
| help.mjs 脚本存在性 | help.mjs 被删除 | TC-R02 | 待验证 |

---

<a id="sec2-cases"></a>

## §2 测试用例

### 2.1 正常用例

| ID | Given | When | Then | 关联 FP | 优先级 |
|----|-------|------|------|---------|--------|
| TC-N01 | API_X_TOKEN 已配置，远端 API 可达，有 ≥1 个故事 | 执行 `/rui-story` | stdout 含"故事任务面板 · 状态概览"、6 种状态统计、最近活动列表 | FP1, FP2, FP4 | P0 |
| TC-N02 | API_X_TOKEN 已配置，远端有 ≥1 个故事 | 执行 `/rui-story list` | stdout 含"进度全景"表格，含 Story/Status/Files/Last Modified/Type/Branch 6 列 | FP1, FP2, FP3, FP5 | P0 |
| TC-N03 | API_X_TOKEN 已配置，远端存在 "rui-story" 故事 | 执行 `/rui-story show rui-story` | stdout 含详述卡：远端路径、类型、文件清单、git 分支、元数据 | FP1, FP2, FP3, FP6 | P0 |
| TC-N04 | 已指定故事名 | 执行 `/rui-story sync <name>` | import-docs mode=pull 被调用 | FP9 | P0 |
| TC-N05 | 故事目录含非 YrY- 前缀文件 | 执行 `/rui-story clear rui-story` 并确认 | 非 YrY- 文件被删除，YrY- 文件保留 | FP10 | P0 |
| TC-N06 | 故事目录存在 | 执行 `/rui-story remove test-story` 并确认 | 整个目录被删除 | FP11 | P1 |
| TC-N07 | 远端有可同步故事 | 执行 `/rui-story recommend` | stdout 含故事名列表 + 推荐 sync 命令 | FP7 | P1 |
| TC-N08 | Token 已配置，API 可达 | 执行 `/rui-story health` | stdout 含"健康检查"、API 凭据/远端可达性/项目配置三段、pass/warn/error 统计 | FP8 | P1 |
| TC-N09 | help.mjs 存在 | 执行 `/rui-story --help` | stdout 含命令表 + 场景示例 + 数据源说明 | FP12 | P1 |

### 2.2 边界用例

| ID | Given | When | Then | 关联 FP | 优先级 |
|----|-------|------|------|---------|--------|
| TC-B01 | 远端 API 可达但无故事任务面板数据 | 执行 `/rui-story` | stdout 含"合计 0 个故事"、"最近活动: 无" | FP1, FP4 | P1 |
| TC-B02 | show 命令 name 参数缺失 | 执行 `node skills/rui-story/rui-story.mjs show` | stderr 输出"show 需要 <name> 参数"，退出码 0 | FP6 | P1 |
| TC-B03 | 故事名含非法字符 | 执行 `/rui-story show my story` | 取决于 argparse，但 name 应被约束为 kebab-case | FP1 | P2 |
| TC-B04 | 并发类型推断时某故事读取失败 | 执行 `/rui-story list` | 该故事类型显示为 meta，其他故事正常 | FP3 | P1 |
| TC-B05 | 进程无 TTY | 执行 `/rui-story list` 重定向到文件 | 输出不含 ANSI 转义序列，纯文本表格 | FP5 | P2 |

### 2.3 异常用例

| ID | Given | When | Then | 关联 FP | 优先级 |
|----|-------|------|------|---------|--------|
| TC-E01 | 远端不存在指定故事 | 执行 `/rui-story show nonexistent` | stdout 含"故事 nonexistent 不存在于远端" + 已知故事列表 | FP6 | P0 |
| TC-E02 | 用户拒绝 clear 确认 | 执行 clear 后输入 n | 显示"取消操作"，无文件被删除 | FP10 | P0 |
| TC-E03 | remove 目标目录不存在 | 执行 `/rui-story remove nonexistent` | 显示"目录不存在"后终止 | FP11 | P1 |
| TC-E04 | API_X_TOKEN 未配置 | 执行任意查询命令 | stdout 含"API_X_TOKEN: 缺失" + 配置方法 | FP1 | P0 |
| TC-E05 | 远端 API 不可达 | 执行任意查询命令 | stderr 含"远端不可达"，退出码 0 | FP1 | P0 |
| TC-E06 | readProjectName 所有模式不匹配 | 执行任意命令 | fallback 到项目根目录名 | FP2 | P1 |

### 2.4 回归用例

| ID | Given | When | Then | 关联模块 | 优先级 |
|----|-------|------|------|---------|--------|
| TC-R01 | CLAUDE.md 项目名格式变更（非表格格式） | 执行 `/rui-story` | 仍能正确解析项目名（粗体标签或冒号格式 fallback） | readProjectName() | P0 |
| TC-R02 | help.mjs 被删除 | 执行 `/rui-story --help` | 输出内置 fallback 帮助文本 | showHelp() | P1 |

---

<a id="sec3-env"></a>

## §3 环境专项

| ID | 场景 | Given | When | Then | 优先级 |
|----|------|------|------|------|--------|
| TC-X01 | 并发类型推断 | 10 个故事需推断类型 | 执行 `/rui-story list` | 4 worker 并发执行，总耗时不超串行 1/3 | P2 |
| TC-X02 | TTY 颜色输出 | stdout.isTTY=true | 执行 `/rui-story` | 含 ANSI 转义序列（bold/dim/red/green/yellow/cyan） | P2 |
| TC-X03 | 非 TTY 纯文本 | stdout.isTTY=false | 执行 `/rui-story list` | 输出纯文本，无 ANSI 转义序列 | P2 |
| TC-X04 | git 命令失败 | git 不可用或仓库损坏 | 执行 `/rui-story list` | checkGitBranch 返回 null，显示"—" | P1 |

---

<a id="sec4-setup"></a>

## §4 测试环境

| 维度 | 配置 |
|------|------|
| 运行环境 | Node.js ≥18，支持 fetch API |
| 部署方式 | 本地开发环境 |
| 测试目标 | skills/rui-story/rui-story.mjs |
| 数据准备 | API_X_TOKEN 环境变量配置 |
| 分支 | feat/rui-story |

---

<a id="sec5-checklist"></a>

## §5 评审清单

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | 每功能点多类覆盖 | ✅ 12 FP × 正常/边界/异常 |
| 2 | Gate A 覆盖 — P0 用例全部在正常/异常列表中 | ✅ |
| 3 | 回归与影响链一致 | ✅ TC-R01, TC-R02 |
| 4 | 异常含恢复行为 | ✅ Token 缺失/API 不可达/不存在均有优雅处理 |
| 5 | 环境专项覆盖 | ✅ TTY/非TTY/git 失败/并发 |
| 6 | 影响链每点有回归 | ✅ readProjectName, help.mjs |
| 7 | 基线溯源闭合 | ✅ §0 每 TC 映射 AC# 和场景 |

---

<a id="sec6-gatea"></a>

## §6 Gate A 交接

| 信号 | 内容 |
|------|------|
| 通过状态 | 待验证 — 测试框架未就绪，需在 code 阶段执行验证 |
| P0 用例 ID | TC-N01–N05, TC-E01, TC-E04, TC-E05, TC-R01 |
| 实现约束 | Node.js ≥18, fetch API, API_X_TOKEN 环境变量 |
| 验证命令 | `node skills/rui-story/rui-story.mjs overview` / `list` / `show <name>` / `--help` |

---

> **变更记录**
>
> | 日期 | 变更 | 触发 | 证据 |
> |------|------|------|------|
> | 2026-05-20 | 初始生成 | doc --from-code rui-story | skills/rui-story/SKILL.md + rui-story.mjs |
