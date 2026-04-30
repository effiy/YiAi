调用 `generate-document` 技能生成或更新文档。

参数：`$ARGUMENTS`

## 命令速查

| 命令 | 作用 |
|------|------|
| `init` | 初始化项目基础文件 + `docs/项目初始化/` 全文档集 |
| `<功能名>-<描述>` | 生成/更新 `docs/<功能名>/` 下文档集（01-05, 07） |
| `weekly [日期]` | 生成/更新本周周报 |
| `from-weekly <周报路径>` | 从周报「后期规划」拆解为多个功能文档集 |

所有命令可反复调用，已存在则增量更新。每次结束必须先 `import-docs` 再 `wework-bot`。

详细规则见 `skills/generate-document/SKILL.md` 与 `README.md`。