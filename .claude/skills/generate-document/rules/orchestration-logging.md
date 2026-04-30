---
paths:
  - "docs/周报/*/logs.md"
  - "docs/周报/*/key-notes.md"
---

# 编排会话日志与关键节点

> 编排阶段状态机与门禁见 `orchestration.md`；核心原则见 `../SKILL.md`。

---

## 1. 交互日志（强制）

每次执行本技能时，每完成一轮交互后，必须追加写入 `docs/周报/<YYYY-MM-DD>~<YYYY-MM-DD>/logs.md`：

| 交互类别 | `--kind` 值 | 示例 |
|----------|-------------|------|
| `.claude/skills/` 下的技能 | `skill` | `import-docs`、`wework-bot` |
| `.claude/agents/` 下的 Agent | `agent` | `docs-retriever`、`doc-impact-analyzer` |
| MCP 工具 | `mcp` | 记录工具标识与调用要点 |
| `.claude/shared/` 契约 | `shared` | `impact-analysis-contract.md` |
| `.claude/` 下的记忆文件 | `memory` | 项目记忆、用户偏好 |
| 其他 | `other` | git 命令、外部脚本 |

### 1.1 记录结构

每条包含：**操作场景**（`--scenario`）、**对话与交互摘要**（`--text` 或 stdin）

### 1.2 评测标注（可选但推荐）

| 参数 | 说明 | 强制程度 |
|------|------|---------|
| `--case good\|bad\|neutral` | 本轮交互质量判定 | 推荐；bad case 建议配合 `--lesson` |
| `--tags "<tag1,tag2>"` | 分类标签 | 可选 |
| `--lesson "<一句后续改进>"` | 对 bad case 的改进建议 | bad case 时推荐 |

### 1.3 命令

```bash
node scripts/log-orchestration.js --skill generate-document \
  --kind <skill|agent|mcp|memory|shared|other> [--name <标识>] \
  [--scenario "<操作场景>"] \
  [--case <good|bad|neutral>] [--tags "<tag1,tag2>"] [--lesson "<后续改进>"] \
  [--text "<单行摘要>"]
```

### 1.4 阻断兜底

即使中途阻断，对已发生的交互仍须补齐日志后再结束，不得静默省略。

---

## 2. 关键节点记录（推荐）

阶段切换、门禁结论、对外通知等里程碑，推荐追加写入 `docs/周报/<YYYY-MM-DD>~<YYYY-MM-DD>/key-notes.md`。

### 2.1 命令

```bash
node scripts/log-key-node.js --title "<节点标题>" \
  [--category <分类，默认 general>] \
  [--skill <关联技能名>] \
  [--text "<说明>"]
```

常用 `--category`：`stage`（阶段切换）、`gate`（门禁结论）、`notify`（对外通知）。

### 2.2 推荐记录时机

| 时机 | `--category` | `--title` 示例 |
|------|-------------|---------------|
| 阶段切换 | `stage` | "阶段 3 完成：doc-architect 已采纳" |
| 门禁结论 | `gate` | "doc-impact-analyzer 门禁通过" |
| 步骤 6 完成 | `notify` | "wework-bot 通知发送成功" |
| 阻断发生 | `gate` | "阶段 2 阻断：影响链未闭合" |

---

## 3. 与周报的关系

- `logs.md` → 编排日志：周报「本周复盘」的根因证据来源
- `key-notes.md` → 关键节点：周报「进展与亮点」的一眼扫描来源

---

## 4. 脚本路径

| 脚本 | 实际路径 |
|------|---------|
| `log-orchestration.js` | `skills/generate-document/scripts/log-orchestration.js` |
| `log-key-node.js` | `skills/generate-document/scripts/log-key-node.js` |