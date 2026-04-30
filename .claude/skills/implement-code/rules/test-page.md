# 测试原型页面规范

> implement-code 阶段 2 中生成的原型页面结构与内容要求。

---

## 1. 核心约束

| 编号 | 约束 |
|------|------|
| T0-1 | 每个场景独立原型页：`tests/e2e/<功能名>/pages/<场景名>/index.html` |
| T0-2 | 页面包含动态检查清单该场景所有 P0 操作步骤的 UI 元素 |
| T0-3 | 所有可交互元素带 `data-testid="<功能名>-<元素描述>"` |
| T0-4 | 页面可通过 `file://` 或 localhost 访问（不依赖登录/路由守卫） |
| T0-5 | 页面顶部注释说明用户故事编号和检查清单章节 |

---

## 2. data-testid 命名

| 元素类型 | 命名模式 | 示例 |
|---------|---------|------|
| 容器 | `<功能名>-container` | `toolbar-container` |
| 按钮 | `<功能名>-<动词>-btn` | `toolbar-download-btn` |
| 输入框 | `<功能名>-<字段名>-input` | `toolbar-filename-input` |
| 结果区域 | `<功能名>-result` | `toolbar-result` |
| 错误提示 | `<功能名>-error-msg` | `toolbar-error-msg` |

---

## 3. 桩行为约束

**允许**：classList.add/remove、textContent 设置、disabled 切换、aria 属性设置
**禁止**：fetch/XMLHttpRequest、引入框架、超过 10 行的领域逻辑函数

---

## 4. 可访问性

- 对话框使用 `role="dialog"` + `aria-modal="true"`
- 错误提示使用 `role="alert"`
- 图标按钮必须有 `aria-label`