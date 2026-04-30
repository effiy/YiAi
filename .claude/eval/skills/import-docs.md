# import-docs 评测示例

真源：`.claude/skills/import-docs/SKILL.md`、`rules/import-contract.md`；脚本：`.claude/skills/import-docs/scripts/import-docs.js`。

**评测约束**：在具备有效 `API_X_TOKEN` 且用户意图为「导入 / 同步到远端」时，预期须执行 **`import-docs.js` 的 `import` 路径**并得到可核对输出（创建 / 覆盖 / 失败计数）；不得以「仅复述命令未运行」作为通过状态。`list` 子命令只列举文件、**不调用远端、不需要 token**，不得以虚构清单冒充脚本输出。不得在回复、日志或仓库文件中写入 token；`X-Token` **仅**从环境变量 `API_X_TOKEN` 读取（不可用 `--token` 传入）。

---

## 用户故事 A：docs 标准导入（配合编排收尾）

**故事**：作为跟进者，希望在 `generate-document` / `implement-code` 结束时，先得到 **真实的** import-docs 统计，再填入 `wework-bot` 的 `☁️ 文档同步`。

**示例输入（对话）**

- 「按 SKILL 标准命令：`--dir docs --exts md`，跑完把创建 N、覆盖 N、失败 N 交给完成通知。」
- 「`docs` 不存在：通知里写跳过导入，不得编造同步数字。」

---

## 用户故事 B：列举后再导入（list → import）

**故事**：作为使用者，希望先用 `list` 看清候选文件，再决定导入范围或前缀。

**示例输入（对话）**

- 「先 `import-docs.js list --dir docs --exts md`，确认列表后再 `import`。」
- 「list 不需要 API_X_TOKEN。」

---

## 用户故事 C：自动检测与 .claude 全量

**故事**：作为维护者，希望在项目根与在 `.claude` 目录下运行时，自动检测规则（md-only vs 全文件）与 SKILL 一致。

**示例输入（对话）**

- 「在项目根执行自动检测：应对项目根 md 或按 SKILL 所述目录逻辑。」
- 「导入 `.claude`：exts 为空表示全文件；路径前缀与空格替换规则见 import-contract。」

---

## 负例（应判不达标）

- 将未执行脚本得到的创建/覆盖/失败数字写入通知或文档。
- 在日志或对话中泄露 `API_X_TOKEN` 或等价明文。
- 用户要求同步远端，但仅以占位文案结束且无真实 `import` 结果（在评测环境允许调用时）。

---

## 使用加强（执行门禁）

- 对话出现「导入 / 同步 / 回传文档同步数字」任一意图时，默认进入 `import` 执行分支，不接受“只给命令不执行”。
- `generate-document` / `implement-code` 收尾时，`import-docs` 结果是 `wework-bot` 的前置门禁；未拿到真实统计不得发送“已同步”口径。
- 建议统一回传格式：`☁️ 文档同步：docs → 远端（创建 N，覆盖 N，失败 N）`；若目录不存在则明确写“跳过导入”。
- 若 `API_X_TOKEN` 缺失，必须回传“未执行同步”的事实状态，禁止编造成功数字。

---

## 与 eval 的关联

- 完成通知与数字顺序：[wework-bot.md](./wework-bot.md)
- 编排侧必须先 import 再通知：[generate-document.md](./generate-document.md)、[implement-code.md](./implement-code.md)
