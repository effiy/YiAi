# 共享组件开发契约

> 共享组件开发规范，作为 `architect`、`code-reviewer` 和 `implement-code` 的共享解释层。

## 1. 什么放共享层，什么放应用层

| 类型 | 位置 | 判断标准 |
|------|------|---------|
| 跨应用共享组件 | `<shared>/components/` | 至少 2 个应用需要 |
| 应用特有组件 | `<app>/components/` | 只在单个应用中使用 |
| 通用工具函数 | `<shared>/utils/` | 不依赖特定应用 Store |
| 应用特有工具 | `<app>/utils/` | 依赖特定应用状态/上下文 |

## 2. 三文件结构

```
<shared>/components/<分类>/<组件名>/
├── index.js       # 组件逻辑（必须）
├── template.html  # 组件模板（必须）
└── index.css      # 组件样式（可选）
```

- **index.js**：使用项目既有的组件注册/导出方式（如 `registerGlobalComponent`），Props 使用对象语法（含 type 和 default），Events 通过 `$emit` 发送
- **template.html**：标准 HTML + Vue 模板语法绑定
- **index.css**：BEM 命名，前缀按项目约定（如 `app-btn--primary`）

## 3. Barrel Export

若项目使用 barrel export，共享组件须在统一入口文件中导出，避免遗漏已开发的组件。

## 4. 组件分类

| 分类 | 路径 | 说明 |
|------|------|------|
| 通用按钮 | `<shared>/components/common/buttons/` | Button, IconButton |
| 通用表单 | `<shared>/components/common/forms/` | Input, Select, Checkbox |
| 通用弹窗 | `<shared>/components/common/modals/` | Modal, Dialog |
| 通用数据展示 | `<shared>/components/common/data-display/` | Table, Tooltip |
| 通用反馈 | `<shared>/components/common/feedback/` | Loading, EmptyState |
| 领域组件 | `<shared>/components/domain/` | 领域特有（若需共享） |

## 5. 与应用入口的衔接

应用入口应在初始化阶段显式声明/注册需要用到的共享组件（方式按项目约定）。

## 6. 安全执行

共享组件内部异步操作建议使用项目统一的错误处理封装（如 `safeExecute`）。

## 7. 检查清单

- 组件位于共享层路径下，不与应用层混放
- 三文件结构完整
- Barrel export 已在统一入口导出（若使用）
- 类名遵循项目 BEM/前缀约定
- 异步操作使用 `safeExecute` 包装
- Props 使用对象语法
- Events 通过 `$emit` 发送，不直接修改父级状态