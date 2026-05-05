调用 `import-docs` 技能将本地文档同步到远程文档 API。

```mermaid
graph LR
    A[/import-docs] --> B{Auto-detect source}
    B -->|.claude/| C[Import all files]
    B -->|other| D[Import .md files]
    C --> E[Execute import-docs.js]
    D --> E
    E --> F[Summarize: new / overwrite / fail]
```

参数: `$ARGUMENTS`

执行要求：
- 无参数时默认使用 `--dir docs --exts md`。
- 必须运行脚本真实的 `import` 路径；不得止步于命令草稿。
- 用户要求"先看列表"时，先跑 `list`，再根据结果 `import`。
- 返回统计：新建 N，覆盖 N，失败 N（或注明 docs 不存在并跳过）。
- 不得明文输出 `API_X_TOKEN`。
