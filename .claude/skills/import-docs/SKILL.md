---
name: import-docs
description: 将本地文档批量同步到远端文档 API。generate-document / implement-code 完成时的强制步骤。
---

# import-docs

## 定位

文档导入技能：自动检测导入源 → 支持 `list` 列举候选 → 执行导入 → 汇总结果供 `wework-bot` 填写真实数字。

## 何时使用

- 用户要求同步/上传/发布/导入文档到远端
- `generate-document` / `implement-code` 完成阶段的强制步骤
- 不触发：只本地生成/修改 Markdown 且用户明确不需同步；目标只是发群通知（走 `wework-bot`）

## 输入

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--dir` | 自动检测 | 导入目录 |
| `--exts` | 自动检测 | 逗号分隔扩展名 |
| `--token` | 仅 `API_X_TOKEN` | **禁用** CLI 参数，仅从系统环境变量读取 |
| `--api-url` | `https://api.effiy.cn` | API 地址 |
| `--prefix` | 空 | 远端路径前缀，逗号分隔 |
| `command` | `import` | `import` 导入文件；`list` 仅列举 |

## 自动检测规则

- 在 `.claude` 下 → 导入 `.claude` 目录，所有文件
- 其他 → 导入项目根目录，仅 `.md` 文件
- `--dir` 指向 `.claude` / `.cursor` 时，`exts` 默认为空（导入所有文件）

## 工作流程

1. 参数解析：从用户请求提取目录、扩展名、前缀
2. 列举候选（可选）：`node scripts/import-docs.js list`
3. 安全检查：不得在回复中展示 token
4. 执行导入：`node scripts/import-docs.js --dir docs --exts md`
5. 结果汇总：发现文件数、created / overwritten / failed 数量
6. 回传通知摘要：`☁️ 文档同步：docs → 远端（创建 N，覆盖 N，失败 N）`

## docs 标准导入（被上游技能调用）

标准命令：`node scripts/import-docs.js --dir docs --exts md`

- 目录存在 → 执行导入，结果写入 wework-bot 通知
- 目录不存在 → 跳过，通知写 `docs 不存在，跳过导入`
- 导入失败 → 不阻断主流程，注明失败数
- `API_X_TOKEN` 缺失 → 记录"未检测到 `API_X_TOKEN`，可后续手动同步"

## 约束

- 默认自动检测，除非用户指定 `--dir` / `--exts`
- 不把 token 写入仓库文件、日志或文档
- 脚本会覆盖远端同路径文件
- 始终忽略 `.git`，不跟随符号链接

## 支持文件

- `rules/import-contract.md`：路径生成、去重、安全约束
- `scripts/import-docs.js`：CLI 实现