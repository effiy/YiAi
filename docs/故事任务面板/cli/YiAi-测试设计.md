# YiAi-测试设计 — cli

> CLI 命令行工具测试设计。1 组件 10 用例。
>
> **来源**：源码分析 | **证据等级**：B | **项目类型**：backend

---

## 测试用例

### TC1–TC5: list 命令

| TC# | 场景 | 预期 |
|-----|------|------|
| TC1 | 无参数默认查询 | 表格显示前 20 条记录 + 分页信息 |
| TC2 | --format json | 输出合法 JSON，含 list/total/pageNum/pageSize/totalPages |
| TC3 | --format csv | 输出 CSV 含表头行 |
| TC4 | --output data.json | 文件写入成功，内容正确 |
| TC5 | --record-type skill_execution | 仅返回该类型记录 |

### TC6–TC7: get 命令

| TC# | 场景 | 预期 |
|-----|------|------|
| TC6 | get 存在的 key | JSON 打印记录内容 |
| TC7 | get 不存在的 key | 红色错误 + exit(1) |

### TC8–TC10: export/stats 命令

| TC# | 场景 | 预期 |
|-----|------|------|
| TC8 | export --output out.json | 文件写入 JSON，page_size=8000 |
| TC9 | export --format csv | 文件写入 CSV 格式 |
| TC10 | stats 无参数 | 显示 Total records 数量 |

---

## Gate A 交接信号

| 检查项 | 状态 |
|--------|:---:|
| AC 全覆盖 (AC1–AC4) | ✓ |
| JSON 输出格式正确 | ✓ (TC2) |
| get 不存在 key 行为 | ✓ (TC7) |
| 文件输出 | ✓ (TC4, TC8) |

---

### 主要价值

- ✅ **10 用例覆盖 4 命令**
- 🎨 **格式测试** — table/json/csv 三种输出均有覆盖
- 📁 **文件输出** — list 和 export 的文件写入
- 🔴 **错误路径** — get 不存在 key 的 exit(1)

---

## 回溯链

| 来源 | 路径 |
|------|------|
| 故事任务 | `YiAi-故事任务.md` §5 |
| 源码 | `src/cli/state_query.py` |

### 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2026-05-22 | 1.0.0 | 初始 /rui doc --from-code |
