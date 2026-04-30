# import-docs 快速索引

`import-docs` 把本地文档批量导入远端文档 API。真源在 `SKILL.md`。

在 `generate-document` / `implement-code` 完成阶段，本 skill 是 `wework-bot` 之前的强制步骤。

## 快速开始

```bash
# 自动检测模式
API_X_TOKEN=*** node .claude/skills/import-docs/scripts/import-docs.js

# 指定目录
API_X_TOKEN=*** node .claude/skills/import-docs/scripts/import-docs.js --dir docs --exts md
```

## 列举 docs 文件（不需要 token）

```bash
node .claude/skills/import-docs/scripts/import-docs.js list
```

## 常用参数

- `--dir, -d`：导入目录（默认：自动检测）
- `--exts, -e`：扩展名（默认：自动检测）
- `--prefix, -p`：远端路径前缀
- `--api-url, -a`：API 地址