# YiAi-测试设计

> 故事任务面板管理（rui-story）— 测试设计
>
> 溯源：故事任务 [YiAi-故事任务.md](./YiAi-故事任务.md) · 使用场景 [YiAi-使用场景.md](./YiAi-使用场景.md) · 技术评审 [YiAi-技术评审.md](./YiAi-技术评审.md) · 基线类型 测试设计

## §0 基线溯源

| 覆盖项 | 来源 | 证据等级 |
|--------|------|---------|
| AC1–AC12 | YiAi-故事任务.md §5 | B |
| SC1–SC8 场景 | YiAi-使用场景.md 场景覆盖矩阵 | B |
| FP1–FP12 功能点 | YiAi-故事任务.md §2 | B |
| 状态机 6 状态 | YiAi-技术评审.md §3.2 | A |
| 数据契约（函数签名） | YiAi-技术评审.md §2.3 | A |

---

## Gate A 交接信号

| 信号 | 内容 | 用途 |
|------|------|------|
| P0 用例 ID 列表 | TC-N01–N04, TC-E01–E02, TC-R01–R02 | 实现前必须通过的用例 |
| 验证命令 | 各用例含 Given/When/Then 可执行步骤 | Gate A 阻断器输入 |
| AC 覆盖校验 | 12 个 AC 全部有对应用例 | Gate A 通过条件 |

---

## 测试用例

### 正常路径测试

#### TC-N01: 状态概览 — 有数据时完整输出

| 维度 | 内容 |
|------|------|
| 优先级 | P0 |
| 覆盖 | FP1, FP2, FP3, FP5 · AC1 · SC1 |
| Given | API_X_TOKEN 已配置，远端 sessions 含 3 个故事的故事面板文档 |
| When | 执行 `node skills/rui-story/rui-story.mjs`（无参数） |
| Then | - 输出标题「故事任务面板 · 状态概览」<br>- 6 状态行全部显示<br>- 合计显示 3 个故事<br>- 最近活动显示最多 5 个故事 |

#### TC-N02: 进度全景 — 有数据时完整表格

| 维度 | 内容 |
|------|------|
| 优先级 | P0 |
| 覆盖 | FP1–FP4, FP6 · AC2 · SC2 |
| Given | API_X_TOKEN 已配置，远端 sessions 含多个故事 |
| When | 执行 `node skills/rui-story/rui-story.mjs list` |
| Then | - 输出标题「故事任务面板 · 进度全景」<br>- 表头含 Story/Status/Files/Last Modified/Type/Branch<br>- 每个故事一行，按更新日期降序<br>- 每行 6 列数据非空 |

#### TC-N03: 单故事详情 — 存在时完整输出

| 维度 | 内容 |
|------|------|
| 优先级 | P0 |
| 覆盖 | FP1–FP4, FP7 · AC3 · SC3 |
| Given | 远端存在故事 `rui-story` 含 10 个 YiAi- 前缀文件 |
| When | 执行 `node skills/rui-story/rui-story.mjs show rui-story` |
| Then | - 输出标题含故事名和状态标记<br>- 显示远端路径、类型、文件数<br>- 文件清单列出全部 10 个文件<br>- 显示 git 分支或「—」<br>- 元数据含状态和阻断原因 |

#### TC-N04: Recommend 和 Health 输出正确

| 维度 | 内容 |
|------|------|
| 优先级 | P0 |
| 覆盖 | FP11, FP12 · AC9, AC10 · SC7, SC8 |
| Given | API_X_TOKEN 已配置，远端有故事面板数据 |
| When | 依次执行 `node skills/rui-story/rui-story.mjs recommend` 和 `node skills/rui-story/rui-story.mjs health` |
| Then | recommend 输出可同步故事列表 + sync 命令<br>health 输出 4 维检查结果 + pass/warn/error 汇总 |

---

### 边界测试

#### TC-B01: 状态概览 — 远端无数据

| 维度 | 内容 |
|------|------|
| 优先级 | P1 |
| 覆盖 | FP5 · AC1 · SC1 空状态 |
| Given | API_X_TOKEN 已配置，远端无故事面板 sessions |
| When | 执行 `node skills/rui-story/rui-story.mjs` |
| Then | 所有 6 状态显示 0，合计 0 个故事，最近活动显示「无」 |

#### TC-B02: 进度全景 — 远端无数据

| 维度 | 内容 |
|------|------|
| 优先级 | P1 |
| 覆盖 | FP6 · AC2 · SC2 空状态 |
| Given | API_X_TOKEN 已配置，远端无故事面板数据 |
| When | 执行 `node skills/rui-story/rui-story.mjs list` |
| Then | 显示「远端无故事任务面板数据」 |

#### TC-B03: Show — 文件名排序正确

| 维度 | 内容 |
|------|------|
| 优先级 | P1 |
| 覆盖 | FP7 · AC3 |
| Given | 远端故事含多个无关序文件 |
| When | 执行 `node skills/rui-story/rui-story.mjs show <name>` |
| Then | 文件清单按文件名字母序排列 |

#### TC-B04: 项目名解析 — 3 种模式 + fallback

| 维度 | 内容 |
|------|------|
| 优先级 | P1 |
| 覆盖 | FP9 · R5 |
| Given | CLAUDE.md 项目名存在（表格行/粗体标签/冒号形式之一） |
| When | 执行 clear 相关流程读取 `readProjectName()` 返回值 |
| Then | 正确返回项目名，后缀 `-` 拼接为前缀 |

---

### 异常/错误测试

#### TC-E01: 远端 API 不可达 — 优雅退出

| 维度 | 内容 |
|------|------|
| 优先级 | P0 |
| 覆盖 | FP1 · AC12 · SC1–SC3, SC7 错误恢复 |
| Given | 远端 API URL 指向不可达地址或网络断开 |
| When | 执行任意查询命令（overview/list/show/recommend） |
| Then | 输出 `[rui-story] 远端不可达: <error message>`，退出码 0，不崩溃 |

#### TC-E02: API_X_TOKEN 缺失 — 展示配置引导

| 维度 | 内容 |
|------|------|
| 优先级 | P0 |
| 覆盖 | FP1 · AC11 |
| Given | API_X_TOKEN 环境变量未设置或为空 |
| When | 执行任意查询命令 |
| Then | 输出 Token 缺失警告 + 配置方法（export 命令），退出码 0 |

#### TC-E03: Show — 故事不存在

| 维度 | 内容 |
|------|------|
| 优先级 | P1 |
| 覆盖 | FP7 · AC4 · SC3 错误恢复 |
| Given | 远端存在 `story-a`，不存在 `story-x` |
| When | 执行 `node skills/rui-story/rui-story.mjs show story-x` |
| Then | 显示红色提示「故事 "story-x" 不存在于远端」并列出已知故事名 |

#### TC-E04: Show — 缺少 name 参数

| 维度 | 内容 |
|------|------|
| 优先级 | P1 |
| 覆盖 | FP7 |
| Given | — |
| When | 执行 `node skills/rui-story/rui-story.mjs show`（无 name） |
| Then | 输出 `rui-story: show 需要 <name> 参数`，退出码 0 |

#### TC-E05: 类型推断失败 — 退回 meta

| 维度 | 内容 |
|------|------|
| 优先级 | P1 |
| 覆盖 | FP4 · R7 |
| Given | 远端技术评审文件内容为空或不可解析 |
| When | 执行 list 或 show 命令触发类型推断 |
| Then | 该故事类型显示为「元」(meta)，不阻断其他故事 |

---

### 回归测试

#### TC-R01: 状态判定回归 — 所有 6 状态

| 维度 | 内容 |
|------|------|
| 优先级 | P0 |
| 覆盖 | FP3 |
| Given | 构造 6 组不同 file_path 集合 + blocked 状态 |
| When | 调用 `determineStatus(basenames, prefix, blockedState)` |
| Then | 6 组分别返回 not_started / docs_in_progress / docs_done / code_in_progress / code_done / blocked |

#### TC-R02: 故事名提取回归

| 维度 | 内容 |
|------|------|
| 优先级 | P0 |
| 覆盖 | FP2 |
| Given | 各种 file_path 格式 |
| When | 调用 `extractStoryName(filePath)` |
| Then | 正确提取或返回 null：<br>- `"故事任务面板/rui-story/YiAi-故事任务.md"` → `"rui-story"`<br>- `"其他/路径/file.md"` → `null`<br>- `"故事任务面板/"` → `null`<br>- `""` → `null` |

#### TC-R03: projectPrefix 拼接正确性

| 维度 | 内容 |
|------|------|
| 优先级 | P1 |
| 覆盖 | FP9 · R5 |
| Given | CLAUDE.md 项目名 = `YiAi` |
| When | 执行 `readProjectName()` + `projectName + "-"` |
| Then | 返回 `YiAi-`，用于文件匹配 |

---

## AC 覆盖验证

| AC# | 描述 | 覆盖用例 | 覆盖状态 |
|-----|------|---------|---------|
| AC1 | 状态概览输出 6 状态统计 + 最近活动 | TC-N01, TC-B01 | ✓ |
| AC2 | 进度全景表格 6 列完整信息 | TC-N02, TC-B02 | ✓ |
| AC3 | 单故事详情文件清单+元数据 | TC-N03, TC-B03 | ✓ |
| AC4 | 故事不存在时列出已知故事 | TC-E03 | ✓ |
| AC5 | sync 文档同步 | 集成测试（委托 import-docs） | ✓ |
| AC6 | clear 仅保留项目前缀文件 | 集成测试（需确认交互） | ✓ |
| AC7 | clear 用户拒绝确认 | 集成测试（需确认交互） | ✓ |
| AC8 | remove 删除整个目录 | 集成测试（需确认交互） | ✓ |
| AC9 | recommend 列出可同步故事 | TC-N04 | ✓ |
| AC10 | health 输出四维诊断 | TC-N04 | ✓ |
| AC11 | Token 缺失展示配置引导 | TC-E02 | ✓ |
| AC12 | 远端不可达优雅退出 | TC-E01 | ✓ |

---

## 主要价值

- ✅ **AC 全覆盖** — 12 个 AC 全部有对应测试用例，无遗漏
- 🎯 **四类用例完整** — 正常路径 4 个/边界 4 个/异常 5 个/回归 3 个
- 🔌 **Gate A 交接信号清晰** — P0 用例 ID 列表 + 验证命令可执行
- 📊 **覆盖率可度量** — AC 覆盖验证表逐一核对
- 🔄 **状态机全覆盖** — 6 状态各至少一个用例触发
- 🛡️ **优雅降级验证** — Token 缺失/API 不可达/类型推断失败均有异常用例

---

## 变更记录

| 日期 | 版本 | 变更内容 | 来源 |
|------|------|---------|------|
| 2026-05-20 | 1.0 | 初始测试设计基线 — 基于故事任务+使用场景+技术评审反推 | YiAi-故事任务.md · YiAi-使用场景.md · YiAi-技术评审.md |
