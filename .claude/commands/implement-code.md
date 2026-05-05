调用 `build-feature` 技能（代码模式）实现代码。

```mermaid
graph LR
    A[/implement-code] --> B[Read feature doc]
    B --> C[Gate A: Test-first]
    C --> D[Gate B: Per-module implement]
    D --> E[Smoke test]
    E --> F[Write §4 report]
    F --> G[import-docs → wework-bot]
```

参数: `$ARGUMENTS`

执行要求：
- 必须基于 `docs/<feature-name>.md` §2 User Stories（每个故事自包含需求+设计+任务+AC）实现；不得在缺少上游文档的情况下凭空编码。
- 完成后必须写入 §4 Project Report，然后执行 `import-docs` → `wework-bot` 收尾。
- 缺少上游文档时，声明缺失路径并中止。
