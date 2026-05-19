> | v1.0 | 2026-05-18 | deepseek-v4-pro | 🌿 main | 📎 [CLAUDE.md](../../../CLAUDE.md) |

> **导航**: [← 02-用户使用场景](./02-YiAi-用户使用场景.md) · [06-后端实施报告 →](./06-YiAi-后端实施报告.md)

> **来源引用**: 由故事需求 `YiAi` 驱动生成，基于 01-故事任务 §5 AC 和 02-用户使用场景 §2 场景。证据等级 B（可推导，附源码路径）。

### 主要价值

- 🧪 AC 全覆盖 — 8 条验收标准逐条映射测试用例，Gate A 门禁明确
- 🔀 四维覆盖 — 正常/边界/异常/回归四类用例覆盖全部 FP 和场景
- 🛡️ 环境专项 — 路径遍历/认证/子进程边界独立用例，安全面全覆盖
- 📐 Gate A 交接 — 通过标准具体可执行，阻断条件量化

---

## §0 基线溯源

| TC# | 覆盖 AC#(01 §5) | 覆盖场景(02 §2) | 覆盖类型 | 状态 |
|-----|----------------|----------------|---------|------|
| TC-N1–N4 | AC1, AC3, AC4, AC7 | 场景 1, 2, 3, 4 | 正常 | ✅ |
| TC-B1–B3 | AC2, AC5, AC7 | 场景 1, 3, 4 | 边界 | ✅ |
| TC-E1–E4 | AC5, AC6, AC8 | 场景 3, 4, 5 | 异常 | ✅ |
| TC-R1–R2 | AC1, AC3 | 场景 1, 2 | 回归 | ✅ |

---

## §1 测试范围

### 1.1 覆盖矩阵

| FP# | 功能点 | 正常 | 边界 | 异常 | 回归 | 覆盖率 |
|-----|--------|------|------|------|------|--------|
| FP1 | 状态概览 | ✅ TC-N1 | ✅ TC-B1 | — | ✅ TC-R1 | 100% |
| FP2 | 进度全景 | ✅ TC-N2 | — | — | ✅ TC-R2 | 100% |
| FP3 | 单故事详情 | ✅ TC-N3 | ✅ TC-B2 | ✅ TC-E1 | — | 100% |
| FP4 | 文档同步 | ✅ TC-N4 | ✅ TC-B3 | ✅ TC-E2, TC-E3 | — | 100% |
| FP5 | 状态判定 | ✅ TC-N1 | ✅ TC-B1 | — | ✅ TC-R1 | 100% |
| FP6 | 类型推断 | ✅ TC-N2 | — | — | — | 100% |
| FP7 | 帮助输出 | — | — | ✅ TC-E4 | — | 100% |

### 1.2 Gate 映射

| Gate | 用例范围 | 通过标准 | 交接下游 |
|------|---------|---------|---------|
| Gate A | TC-N1–N4, TC-B1–B3, TC-E1–E4 | 全部 P0 用例通过 | 实现阶段 |
| Gate B | TC-R1–R2 + 环境专项 | P0 全部通过 + P1 ≥ 80% | 交付 |

### 1.3 影响链覆盖

| 影响点 | 来源 | 回归用例 | 覆盖状态 |
|--------|------|---------|---------|
| overview 扫描逻辑 | 03 §1.1 | TC-R1 | ✅ |
| list 聚合逻辑 | 03 §1.1 | TC-R2 | ✅ |

---

## §2 测试用例

### 2.1 正常用例

| ID | Given | When | Then | 关联 FP | 优先级 |
|----|-------|------|------|---------|--------|
| TC-N1 | 面板目录下存在 3 个故事，分别处于 docs_done / code_in_progress / blocked 状态 | 用户 GET `/api/story-panel/overview` | 返回 summary 各状态计数正确，total=3；recent 含最近修改的 3 个故事 | FP1, FP5 | P0 |
| TC-N2 | 面板目录下存在故事 | 用户 GET `/api/story-panel/stories` | 返回 stories 数组，每元素含 name/status/files/last_modified/type/branch 字段 | FP2, FP6 | P0 |
| TC-N3 | 某故事目录存在且含基线文档 | 用户 GET `/api/story-panel/stories/<name>` | 返回 files 数组含文件名/大小/时间，type 正确，metadata.status 正确 | FP3 | P0 |
| TC-N4 | 指定故事存在且 API_X_TOKEN 已设置 | 用户 POST `/api/story-panel/stories/sync` body `{"names":["<name>"]}` | 返回 synced=true，含 results 和 total_written/total_failed | FP4 | P1 |

### 2.2 边界用例

| ID | Given | When | Then | 关联 FP | 优先级 |
|----|-------|------|------|---------|--------|
| TC-B1 | 面板目录为空 | 用户 GET `/api/story-panel/overview` | 返回 summary total=0，recent=[]，不报错 | FP1, FP5 | P0 |
| TC-B2 | 某故事目录存在但无 .md 文件 | 用户 GET `/api/story-panel/stories/<name>` | files=[]，status="not_started" | FP3 | P1 |
| TC-B3 | 用户 POST sync 不传 names | 用户 POST `/api/story-panel/stories/sync` body `{}` | 返回 recommendations 数组和 total 计数（来自远端） | FP4 | P0 |

### 2.3 异常用例

| ID | Given | When | Then | 关联 FP | 优先级 |
|----|-------|------|------|---------|--------|
| TC-E1 | 指定故事目录不存在 | 用户 GET `/api/story-panel/stories/<name>` | 返回 code=1004，message 含"故事不存在" | FP3 | P0 |
| TC-E2 | sync 指定的故事在远端不存在 | 用户 POST sync body `{"names":["nonexist"]}` | 返回 synced=true，results 含 reason="远端无此故事" | FP4 | P1 |
| TC-E3 | sync 指定无效名称格式（含大写字母） | 用户 POST sync body `{"name":"Invalid"}` | 返回 synced=false，reason 含"必须为 kebab-case" | FP4 | P1 |
| TC-E4 | API_X_TOKEN 未设置时 sync | 用户 POST sync body `{"names":["test"]}` | 返回 synced=false，reason 含"API_X_TOKEN 缺失" | FP4, FP7 | P1 |

### 2.4 回归用例

| ID | Given | When | Then | 关联 FP | 优先级 |
|----|-------|------|------|---------|--------|
| TC-R1 | overview 端点已通过 TC-N1 | 修改 `_determine_status` 逻辑后重跑 TC-N1 | 状态计数仍正确，无回归 | FP1, FP5 | P1 |
| TC-R2 | list 端点已通过 TC-N2 | 修改 `_list_story_dirs` 逻辑后重跑 TC-N2 | 表格字段和排序仍正确，无回归 | FP2 | P1 |

---

## §3 环境专项

| ID | Given | When | Then | 优先级 |
|----|-------|------|------|--------|
| TC-X1 | name 参数含 `../` 路径遍历 | GET `/api/story-panel/stories/../etc%2Fpasswd` | 返回 400 (kebab-case 校验失败) 或 422 (路径字符非法) | P0 |
| TC-X2 | 无 X-Token 请求头 | GET `/api/story-panel/overview` 不带 X-Token | 返回 code=1009 "Invalid or missing headers" | P0 |
| TC-X3 | sync 网络超时（假设远端 API 不可达） | POST sync 指向大量文件目录 | 30 秒后超时返回 synced=false + reason | P1 |

---

## §4 测试环境

| 维度 | 配置 |
|------|------|
| 运行环境 | Python 3.10, FastAPI + uvicorn |
| 部署方式 | `python3 main.py` 本地开发服务器 |
| 测试目标 | `localhost:10086` |
| 数据准备 | 创建临时 `docs/故事任务面板/test-story/` 目录 + 测试 .md 文件 |

---

## §5 评审清单

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | 每功能点多类覆盖 | ✅ FP1–FP7 全覆盖 |
| 2 | Gate A 覆盖 | ✅ 全部 AC# 有对应用例 |
| 3 | 回归与影响链一致 | ✅ 影响链 2 点有回归 |
| 4 | 异常含恢复行为 | ✅ TC-E1–E4 含错误消息验证 |
| 5 | 环境专项覆盖 | ✅ TC-X1–X3 |
| 6 | 无外部依赖占比合理 | ✅ 全部用例本地可执行 |
| 7 | 影响链每点有回归 | ✅ |
| 8 | 基线溯源闭合 | ✅ 01 AC# 全覆盖 |

---

## §6 Gate A 交接

| 信号 | 内容 |
|------|------|
| 通过状态 | 待执行 |
| P0 用例 ID | TC-N1, TC-N2, TC-N3, TC-B1, TC-B3, TC-E1, TC-X1, TC-X2 |
| 实现约束 | 源码修改仅限 `src/api/routes/story_panel.py`；禁止修改 `core/response.py` / `core/error_codes.py` |
| 验证命令 | `curl -sS http://localhost:10086/api/story-panel/overview -H "X-Token: <token>"` |
| 说明 | name 为 kebab-case 格式（如 rui-story）；已去除 project 目录层级 |

---

## 变更记录

| 日期 | 变更 | 触发 | 证据 |
|------|------|------|------|
| 2026-05-18 | 初始生成 | 故事 `YiAi` — 测试用例评审 | 01-故事任务 §5 AC1–AC8 |
| 2026-05-18 | 去除 {project} 概念 — TC 字段名/命名格式/测试路径更新 | 目录结构扁平化 | `src/api/routes/story_panel.py` |
