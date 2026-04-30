# MCP 降级契约

> `generate-document` 与 `implement-code` 的 MCP 降级策略。

## 1. 总原则

- MCP 不可用不得阻断流程：所有 MCP 都须有降级方案
- 禁止静默降级：所有降级须记录到 `06_实施总结.md` 或 `docs/99_agent-runs/`
- 探针先行：阶段 0 须检测 MCP 可用性，提前声明降级状态
- 降级记录格式：`MCP 降级：<名称> — <工具> — 原因：<原因> — 降级方案：<方案> — 影响：<影响>`

## 2. 降级映射

| MCP | 工具 | 降级方案 | 可阻断 |
|-----|------|---------|--------|
| `playwright` | 浏览器操作 | `npx playwright test` + 人工确认 | 否 |
| `code-analyzer-mcp` | `analyze_dependencies` | Grep 搜索 import/export + Read 文件头 | 否 |
| `code-analyzer-mcp` | `find_usages` | Grep 全项目搜索标识符 | 否 |
| `code-analyzer-mcp` | `check_architecture` | Read Store/组件注册 + 人工模式匹配 | 否 |
| `code-analyzer-mcp` | `detect_dead_code` | Grep 导出名 + Grep 引用次数 | 否 |
| `doc-index-mcp` | `search_docs` | Grep 搜索 `docs/` 内容 | 否 |
| `doc-index-mcp` | `get_doc_structure` | Read 文件 + 提取 `##` 标题 | 否 |
| `doc-index-mcp` | `find_cross_refs` | Grep 搜索 `[` 和 `](` 模式 | 否 |
| `doc-index-mcp` | `validate_links` | Read + Glob 验证路径存在性 | 否 |
| `git-workflow-mcp` | `create_feature_branch` | Bash `git checkout -b feat/<name>` | 否 |
| `git-workflow-mcp` | `get_diff_summary` | Bash `git diff --stat` + `--name-status` | 否 |
| `git-workflow-mcp` | `analyze_change_impact` | 退回 `impact-analyst` 的 Grep 方案 | 否 |
| `git-workflow-mcp` | `check_branch_status` | Bash `git status` + `git log` | 否 |

## 3. 探针检查

阶段 0 须对每个 MCP 执行最小可行探针：

| MCP | 探针方法 | 通过条件 |
|-----|---------|---------|
| `code-analyzer-mcp` | 调用 `analyze_dependencies` 传入入口文件 | 返回非空依赖列表 |
| `doc-index-mcp` | 调用 `search_docs` 搜索 `README` | 返回结果或"未找到" |
| `git-workflow-mcp` | 调用 `check_branch_status` | 返回当前分支信息 |
| `playwright` | 打开 `about:blank` | 页面成功加载 |

通过则正常使用；失败则记录原因 → 激活降级方案 → 在阶段 0 产出中声明降级状态。

## 4. 降级记录

**记录位置**：`06_实施总结.md` 的「MCP 明细」章节；未到阶段 7 时写入 `docs/99_agent-runs/`

**wework-bot 通知**：正常 `🧩 MCP 明细：<MCP1> ✅ / <MCP2> ✅`；降级 `🧩 MCP 明细：<MCP1> ⚠️ 降级(<方案>)`

## 5. 与其他共享规范的关系

- 降级记录须遵守 `evidence-and-uncertainty.md` 真值层级（降级效果为 C 类）
- `impact-analyst` 使用降级方案时须在产物中标注降级状态
- `impl-reporter` 生成总结时须在 Mermaid 图中用虚线框标注降级节点