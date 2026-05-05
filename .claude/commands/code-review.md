调用 `code-review` 技能审查代码是否符合规范。

```mermaid
graph LR
    A[/code-review] --> B[Read target code]
    B --> C[Run review dimensions]
    C --> D{Grade issues}
    D -->|P0| E[Block release]
    D -->|P1| F[Suggest fix]
    D -->|P2| G[Optional optimize]
    E --> H[Output graded report]
    F --> H
    G --> H
```

参数: `$ARGUMENTS`

执行要求：
- 必须基于真实读取的代码进行审查；不得推断未读文件的内容。
- 审查维度：项目专项（入口初始化、状态管理、组件注册/导出、代码结构）+ 通用质量（可读性、边界、安全、性能）。
- 输出按 P0/P1/P2 分级，附文件路径和修复建议。
- 文件无法读取时，声明路径并跳过。
