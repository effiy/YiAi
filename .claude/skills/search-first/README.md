# search-first 快速索引

`search-first` 用于在做技术决策（选库、选方案）前先并行搜索 npm / PyPI / MCP / GitHub / Web，用真实数据支撑决策。行为真源在 `SKILL.md`。

## 快速开始

```bash
/search-first <需求描述> [约束条件]
```

示例：

```bash
/search-first "前端图表库，支持大数据量渲染" "Vue3,MIT"
/search-first "Node.js ORM" "TypeScript,活跃维护"
```

## 文件职责

| 文件           | 职责                           |
| -------------- | ------------------------------ |
| `SKILL.md`     | 搜索范围、评估矩阵、决策规则   |

## 搜索范围

- `npm` / `PyPI`：包名、周下载量、最后更新
- `GitHub`：stars、open issues、最后 commit
- `MCP`：可用 MCP 工具
- `Web`：最新文档、已知问题、社区评价

## 使用原则

1. 所有推荐必须有可验证来源（URL / 包名@版本）。
2. 搜索结果与需求不符时，输出"未找到满足约束的方案"，不猜测。
3. 若无网络访问权限，明确说明"无法执行搜索，以下为基于训练数据的参考（可能过时）"。
