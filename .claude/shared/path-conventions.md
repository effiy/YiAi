# 路径与链接约定

本文档统一 `.claude` 体系中的路径写法，避免出现旧目录模型和失效链接。

## 稳定入口

- 技能目录：`.claude/skills/<skill-name>/`
- 技能真源：`.claude/skills/<skill-name>/SKILL.md`
- 代理目录：`.claude/agents/<agent-name>.md`
- 命令目录：`.claude/commands/<command-name>.md`
- 评测示例：`.claude/eval/skills/<skill>.md`、`eval/agents/<agent>.md`（用户故事与示例输入；首期 `skills/wework-bot.md`、`agents/message-pusher.md`，非技能真源）

## 禁止使用的旧路径

以下写法已废弃，不应再出现在任何规则、模板或 README 中：

- `.claude/skills/generate-document.md`
- `.claude/rules/...`
- `.claude/templates/...`
- `.claude/skills/checklist/...`

## 推荐写法

### 在 `docs/` 文档中引用 `.claude`

从 `docs/` 下不同深度的文档回链到 `.claude` 时，使用从当前位置到仓库根目录的相对路径：

- **2 级深度**（如 `docs/<功能名>/`）：`../../.claude/skills/generate-document/SKILL.md`
- **3 级深度**（如 `docs/周报/<自然周>/`）：`../../../.claude/skills/generate-document/SKILL.md`
- **4 级深度**（如更深嵌套）：逐级增加 `../`

示例：

- `../../.claude/skills/generate-document/SKILL.md`（2 级）
- `../../.claude/skills/generate-document/rules/需求文档.md`（2 级）
- `../../../.claude/skills/generate-document/SKILL.md`（3 级，周报目录内）

### 兜底路径

当 skill 因缺少参数、目标目录不可定位或前置材料缺失而无法写入目标产物时，仍必须写入：

- `docs/99_agent-runs/<YYYYMMDD-HHMMSS>_<skill-name>.md`

### 在 `.claude` 内部互相引用

优先使用基于当前文件位置可直接解析的相对路径，不额外制造别名目录。

## 链接治理规则

- 只链接到仓库里真实存在的 skill、agent、rule、template、checklist、eval 示例文档。
- 若某能力没有对应 skill 或 agent，应明确写“未提供专用入口”，而不是编造名字。
- 目录结构调整后，必须做一次全仓 `.claude/` 链接回归搜索。
