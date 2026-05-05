调用 `build-feature` 技能（文档模式）生成或更新文档。

```mermaid
graph TD
    A[/generate-document] --> B{Command}
    B -->|init| C[Initialize project docs]
    B -->|feature-name| D[Generate §1-§4 + postscript]
    B -->|weekly| E[Generate weekly report]
    B -->|from-weekly| F[Decompose into features]
    C --> G[import-docs → wework-bot]
    D --> G
    E --> G
    F --> G
```

参数: `$ARGUMENTS`

## 命令速查

| 命令 | 用途 |
|---------|---------|
| `init` | 初始化项目基础文件 + 完整 `docs/project-init/` 文档集 |
| `<feature-name>-<description>` | 生成/更新单一文档 `docs/<feature-name>.md`（§1–§4 + 后记），以故事为单位组织 |
| `weekly [date]` | 生成/更新本周周报 |
| `from-weekly <weekly-path>` | 将周报中的"未来规划"分解为多个功能文档 |

所有命令均为幂等；已有文档增量更新。每次运行必须以 `import-docs` 结束，再以 `wework-bot` 结束。

完整规则参见 `skills/build-feature/SKILL.md` 和 `README.md`。
