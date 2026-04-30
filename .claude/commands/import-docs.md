调用 `import-docs` 技能将本地文档同步到远端文档 API。

参数：`$ARGUMENTS`

执行要求：
- 无参数时默认 `--dir docs --exts md`
- 须走脚本真实 `import` 路径，不得只给命令草稿
- 要求"先看清单"时先执行 `list`，再按结果执行 `import`
- 返回统计：创建 N、覆盖 N、失败 N（或说明 docs 不存在而跳过）
- 不得输出 `API_X_TOKEN` 明文