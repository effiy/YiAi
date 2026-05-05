调用 `search-first` 技能在技术决策前评估候选方案。

```mermaid
graph LR
    A[/search-first] --> B[Parse requirements]
    B --> C[Parallel search]
    C --> C1[npm/PyPI]
    C --> C2[GitHub]
    C --> C3[Web]
    C1 --> D[Build evaluation matrix]
    C2 --> D
    C3 --> D
    D --> E[Recommend with evidence]
```

参数: `$ARGUMENTS`

执行要求：
- 必须基于真实搜索数据给出建议，附可验证来源（URL / package@version）。
- 评估矩阵须覆盖功能覆盖度、维护活跃度、社区规模、许可证。
- 结果不满足需求时，输出"未找到满足约束的方案"——不得虚构。
- 无网络访问时，声明"无法执行搜索；以下为基于训练数据的参考（可能过时）"。
