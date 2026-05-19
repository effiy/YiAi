> | v1.0 | 2026-05-18 | deepseek-v4-pro | 🌿 main | 📎 [01-故事任务 ←](./YiWeb-01-故事任务.md) |

> **导航**: [← 01-故事任务](./YiWeb-01-故事任务.md) | [← 02-用户使用场景](./YiWeb-02-用户使用场景.md) | [05-测试用例评审 →](./YiWeb-05-测试用例评审.md)

> **来源引用**: 由 [YiWeb-01-故事任务](./YiWeb-01-故事任务.md) §1 Story 1–6 驱动。外部参考吸收自 ui-ux-pro-max（Soft UI + Swiss 设计系统 · 可访问性预交付检查表）· system-design-primer（深模块设计 · 纵深防御）。证据等级 A（源码可验证，附路径）。

---

## §0 架构全景

```mermaid
flowchart TB
    subgraph Browser["浏览器运行时"]
        subgraph Entry["入口层"]
            HTML["index.html<br/>视图入口"]:::entry
            Config["环境配置<br/>local / prod 切换"]:::entry
        end

        subgraph Framework["视图框架层"]
            BaseView["createBaseView<br/>统一应用工厂"]:::framework
            Loader["componentLoader<br/>全局组件注册"]:::framework
            Registry["ComponentRegistry<br/>组件发现与缓存"]:::framework
        end

        subgraph Views["视图层 (src/views/)"]
            AICR["AICR 视图<br/>代码审查 · AI 对话<br/>22 组件 · 60+ 状态"]:::view
            StoryPanel["storyPanel 视图<br/>故事任务面板<br/>4 组件 · 5 状态"]:::view
        end

        subgraph CDN["CDN 组件与工具 (cdn/)"]
            Comps["通用组件<br/>YiButton · YiModal · YiTag<br/>YiSelect · YiLoading 等"]:::cdn
            Markdown["Markdown 渲染器<br/>插件管道<br/>Sanitize · Mermaid · TOC"]:::cdn
            Utils["工具库<br/>日志 · 错误 · DOM · 事件<br/>存储 · 验证 · 动画"]:::cdn
        end

        subgraph Services["服务层 (src/core/services/)"]
            Helper["辅助层<br/>fetch 封装 · 认证 · 401 处理"]:::service
            Modules["模块层<br/>CRUD · Goals 服务"]:::service
            Business["业务层<br/>流程管理 · 场景分析"]:::service
        end
    end

    subgraph Backend["后端服务"]
        API["api.effiy.cn<br/>统一 API 网关"]:::backend
        Data["data.effiy.cn<br/>数据服务"]:::backend
        Ollama["ollama.effiy.cn<br/>AI 模型服务"]:::backend
    end

    Entry --> Framework
    Framework --> Views
    Views --> CDN
    Views --> Services
    Services --> Helper
    Helper --> Modules
    Helper --> Business
    Helper --> API
    Helper --> Data
    AICR --> Ollama

    classDef entry fill:#f3e5f5,stroke:#6a1b9a;
    classDef framework fill:#e8eaf6,stroke:#3f51b5;
    classDef view fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef cdn fill:#e8f5e9,stroke:#2e7d32;
    classDef service fill:#fff3e0,stroke:#e65100;
    classDef backend fill:#eceff1,stroke:#607d8b;
```

---

## §1 视图架构

### 1.1 视图工厂模式

YiWeb 使用自研 `createBaseView` 函数作为统一的视图工厂，语义类似 Vue Options API：

```mermaid
flowchart LR
    subgraph 输入["createBaseView 输入"]
        Store["createStore<br/>响应式状态工厂"]:::in
        Computed["useComputed<br/>计算属性"]:::in
        Methods["useMethods<br/>方法集合"]:::in
        Comps["components<br/>组件名列表"]:::in
        Modules["componentModules<br/>组件 JS 路径"]:::in
        Data["data<br/>模板绑定数据"]:::in
        Mounted["onMounted<br/>挂载回调"]:::in
    end

    subgraph 处理["视图工厂处理"]
        Wait["轮询等待组件注册<br/>超时 60s"]:::proc
        Create["Vue.createApp<br/>创建应用实例"]:::proc
        Mount["mount('#app')<br/>挂载到 DOM"]:::proc
    end

    subgraph 输出["运行时产物"]
        App["window.storyPanelApp<br/>或 window.aicrApp"]:::out
        StoreObj["window.*Store<br/>全局可访问的 store"]:::out
    end

    输入 --> Wait --> Create --> Mount --> 输出

    classDef in fill:#e3f2fd,stroke:#1565c0;
    classDef proc fill:#fff3e0,stroke:#e65100;
    classDef out fill:#e8f5e9,stroke:#2e7d32;
```

| 配置项 | 类型 | 说明 |
|------|------|------|
| `createStore` | `() => store` | 返回包含 ref 和方法的 store 对象 |
| `useComputed` | `(store) => computed` | 返回计算属性集合 |
| `useMethods` | `(store) => methods` | 返回方法集合 |
| `components` | `string[]` | 模板中使用的组件名列表（PascalCase） |
| `componentModules` | `string[]` | 对应组件 JS 文件的 CDN/本地路径 |
| `data` | `object` | 绑定到模板的响应式数据 |
| `onMounted` | `() => void` | 应用挂载后回调 |

**源码路径**: `/cdn/utils/view/baseView.js` — `createBaseView()` (≈200 行)

### 1.2 组件注册系统

```mermaid
flowchart TB
    subgraph 注册["registerGlobalComponent()"]
        R1["指定 name<br/>组件名 (PascalCase)"]:::reg
        R2["指定 html<br/>模板文件路径"]:::reg
        R3["指定 css<br/>样式文件路径（可选）"]:::reg
        R4["声明 props<br/>类型 + 默认值"]:::reg
        R5["声明 emits<br/>事件列表"]:::reg
        R6["定义 data/computed<br/>/methods"]:::reg
    end

    subgraph 加载["组件加载器"]
        L1["异步 fetch HTML 模板"]:::load
        L2["内存 + localStorage 缓存"]:::load
        L3["CSS 注入（去重）"]:::load
        L4["挂载到 window[Name]"]:::load
    end

    subgraph 消费["模板中使用"]
        U1["<kebab-case> 标签"]:::use
        U2[":prop 传参"]:::use
        U3["@event 监听"]:::use
    end

    注册 --> 加载 --> 消费

    classDef reg fill:#e3f2fd,stroke:#1565c0;
    classDef load fill:#fff3e0,stroke:#e65100;
    classDef use fill:#e8f5e9,stroke:#2e7d32;
```

**源码路径**: `/cdn/utils/view/componentLoader.js` — `registerGlobalComponent()` + `defineComponent()` (≈150 行)

### 1.3 组件分类

| 类别 | 位置 | 示例 | 注册方式 |
|------|------|------|---------|
| 通用组件 | `cdn/components/common/` | YiButton, YiModal, YiTag, YiSelect | 全局注册（CDN index.js） |
| 业务组件 | `cdn/components/business/` | MarkdownView, SearchHeader, SkeletonLoader | 全局注册（CDN index.js） |
| 视图业务组件 | `src/views/<name>/components/` | StoryPanelPage, AicrPage, FileTree | 视图入口注册 |

---

## §2 状态管理

### 2.1 Store 工厂模式

```mermaid
flowchart TB
    subgraph Store["createStore() — 状态工厂"]
        State["Vue ref 定义<br/>loading · error · data<br/>selectedStory · syncing"]:::state
        Actions["异步操作<br/>fetchStories()<br/>selectStory() · syncStory()"]:::action
        Return["返回 { refs, actions }<br/>扁平对象，无嵌套"]:::ret
    end

    subgraph Computed["useComputed(store)"]
        C1["statusCounts<br/>六状态聚合计数"]:::comp
        C2["totalStories<br/>故事总数"]:::comp
        C3["filteredStories<br/>本地搜索过滤"]:::comp
    end

    subgraph Methods["useMethods(store)"]
        M1["模板事件回调<br/>viewStory · goBack"]:::method
        M2["格式化函数<br/>formatDate · typeLabel"]:::method
    end

    State --> Actions
    Actions --> Return
    Return --> Computed
    Return --> Methods

    classDef state fill:#e3f2fd,stroke:#1565c0;
    classDef action fill:#fff3e0,stroke:#e65100;
    classDef ret fill:#e8f5e9,stroke:#2e7d32;
    classDef comp fill:#f3e5f5,stroke:#6a1b9a;
    classDef method fill:#e8eaf6,stroke:#3f51b5;
```

| 约束 | 规则 |
|------|------|
| 单向数据流 | 组件事件 → methods → store mutation → computed 重算 → DOM 更新 |
| ref 只读 | 组件禁止直接修改 ref，所有变更走 store 方法 |
| computed 无副作用 | 计算属性仅读取状态，不触发 API 调用或 DOM 操作 |
| API 调用隔离 | 网络请求仅在 store actions 中执行 |

**源码路径**: `src/views/storyPanel/hooks/store.js` — 故事面板 store (211 行)；`src/views/aicr/hooks/state/storeFactory.js` — AICR store 工厂 (复合 4 子模块)

### 2.2 故事六状态判定模型

```mermaid
flowchart TD
    START["检查故事目录"] --> Q1{"有 01-故事任务?"}
    Q1 -->|"否"| NS["not_started<br/>未开始"]:::s0
    Q1 -->|"是"| Q2{"有 02 + 05 + (03 或 04)?"}
    Q2 -->|"否"| DIP["docs_in_progress<br/>文档进行中"]:::s1
    Q2 -->|"是"| Q3{"有 06 或 07?"}
    Q3 -->|"否"| DD["docs_done<br/>文档完成"]:::s2
    Q3 -->|"是"| Q4{"有 08?"}
    Q4 -->|"否"| CIP["code_in_progress<br/>编码进行中"]:::s3
    Q4 -->|"是"| CD["code_done<br/>编码完成"]:::s4

    classDef s0 fill:#eceff1,stroke:#90a4ae;
    classDef s1 fill:#fff3e0,stroke:#e65100;
    classDef s2 fill:#e8f5e9,stroke:#388e3c;
    classDef s3 fill:#e3f2fd,stroke:#1565c0;
    classDef s4 fill:#c8e6c9,stroke:#2e7d32;
```

**源码路径**: `src/views/storyPanel/hooks/store.js:55–76`

---

## §3 API 通信层

### 3.1 请求管道

```mermaid
flowchart LR
    Call["视图调用<br/>store.fetchStories()"]:::src --> Wrapper["sendRequest()<br/>统一 fetch 封装"]:::pipe
    Wrapper --> Intercept["请求拦截<br/>注入 X-Token 头"]:::pipe
    Intercept --> Fetch["fetch(url, config)<br/>credentials: 'omit'"]:::pipe
    Fetch --> Race["竞速: 请求 vs 超时<br/>默认 5min"]:::pipe
    Race --> Check{"响应状态?"}
    Check -->|"2xx"| Parse["JSON 解析"]:::ok
    Check -->|"401"| Handle401["清除 Token<br/>弹出重新输入<br/>自动重试"]:::warn
    Check -->|"其他 4xx/5xx"| Error["错误分类<br/>超时/网络/CORS"]:::err
    Parse --> Cache["内存缓存<br/>5min TTL · 100 项"]:::ok
    Parse --> Return["返回 data"]:::ok

    classDef src fill:#e8f5e9,stroke:#2e7d32;
    classDef pipe fill:#e3f2fd,stroke:#1565c0;
    classDef ok fill:#e8f5e9,stroke:#2e7d32;
    classDef warn fill:#fff3e0,stroke:#e65100;
    classDef err fill:#ffebee,stroke:#c62828;
```

**源码路径**:
- `src/core/services/helper/requestHelper.js` — `sendRequest()` (≈200 行)
- `src/core/services/helper/authUtils.js` — `getAuthHeaders()` (≈100 行)
- `src/core/services/helper/authErrorHandler.js` — `handle401Error()` (≈80 行)
- `src/core/services/modules/crud.js` — `getData()` / `postData()` / `streamPrompt()` (≈400 行)

### 3.2 API 端点契约

| 端点 | 方法 | 用途 | 认证 |
|------|------|------|:---:|
| `{API_URL}/` | POST | 通用数据操作（query/create/update/delete document） | X-Token |
| `{API_URL}/read-file` | POST | 读取远端文件内容 | X-Token |
| `{API_URL}/write-file` | POST | 写入文件到远端 | X-Token |
| `{API_URL}/upload/upload-image-to-oss` | POST | 上传图片到 OSS | X-Token |
| `{OLLAMA_URL}/api/tags` | GET | 获取可用 AI 模型列表 | — |

### 3.3 流式对话协议

```mermaid
flowchart LR
    Send["发送消息"]:::src --> SSE["SSE 连接<br/>text/event-stream"]:::proto
    SSE --> Parse{"协议检测"}
    Parse -->|"新版"| Type["type 字段路由<br/>text / think / tool_call"]:::proto
    Parse -->|"旧版"| Legacy["fromSystem / fromUser<br/>字段路由"]:::proto
    Type --> Render["流式渲染<br/>逐字追加到 DOM"]:::render
    Legacy --> Render
    Render --> Post["后处理<br/>&lt;think&gt; 剥离<br/>代码栅栏提取<br/>JSON 规范化"]:::render

    classDef src fill:#e8f5e9,stroke:#2e7d32;
    classDef proto fill:#e3f2fd,stroke:#1565c0;
    classDef render fill:#f3e5f5,stroke:#6a1b9a;
```

**源码路径**: `src/core/services/modules/crud.js:streamPrompt()` (≈150 行)

---

## §4 Markdown 渲染管道

### 4.1 插件架构

```mermaid
flowchart TB
    Input["Markdown 文本"]:::src --> Parser["Markdown 解析器<br/>CDN marked.js"]:::core
    Parser --> Pipeline["插件管道（顺序执行）"]:::core

    subgraph Pipeline["插件管道"]
        FM["FrontmatterPlugin<br/>前置元数据提取"]:::plugin
        Container["ContainersPlugin<br/>::: tip/warning/danger"]:::plugin
        Acc["AccordionPlugin<br/>可折叠块"]:::plugin
        TOC["TocPlugin<br/>目录生成"]:::plugin
        Cell["TableCellMarkdownPlugin<br/>表格内联渲染"]:::plugin
        Mermaid["MermaidPlugin<br/>图表代码块 → SVG"]:::plugin
        Link["InternalLinkPlugin<br/>内部链接可点击"]:::plugin
        Sanitize["SanitizePlugin<br/>HTML 净化 · XSS 防护"]:::plugin
    end

    Parser --> Output["安全 HTML"]:::out
    Output --> DOM["浏览器渲染"]:::out

    classDef src fill:#e8f5e9,stroke:#2e7d32;
    classDef core fill:#e3f2fd,stroke:#1565c0;
    classDef plugin fill:#fff3e0,stroke:#e65100;
    classDef out fill:#e8f5e9,stroke:#2e7d32;
```

**源码路径**: `/cdn/markdown/core/MarkdownRenderer.js` (≈120 行) + `/cdn/markdown/core/PluginSystem.js` (≈80 行)

### 4.2 Mermaid 图表增强

| 插件 | 功能 | 交互 |
|------|------|------|
| ToolbarPlugin | 缩放控件工具栏 | 点击放大/缩小/重置 |
| FullscreenPlugin | 全屏查看 | 点击全屏图标 |
| DownloadPlugin | SVG/PNG 下载 | 点击下载按钮 |
| ClipboardPlugin | 复制图表代码 | 点击复制按钮 |
| AIFixPlugin | 图表语法自动修复 | 渲染失败时自动重试 |

**源码路径**: `/cdn/mermaid/core/MermaidRenderer.js` (≈200 行) + `/cdn/mermaid/core/MermaidConfig.js` (≈60 行)

---

## §5 安全架构

### 5.1 纵深防御模型

```mermaid
flowchart TB
    subgraph 输入层["输入层"]
        I1["URL 参数<br/>?env= · ?key= · ?tag="]:::layer
        I2["用户输入<br/>对话消息 · 搜索词"]:::layer
        I3["文件上传<br/>项目 ZIP 导入"]:::layer
    end

    subgraph 传输层["传输层"]
        T1["credentials: 'omit'<br/>不发送 Cookie"]:::layer
        T2["X-Token 头<br/>仅 localStorage 存储"]:::layer
        T3["CORS 模式<br/>无通配符 Origin"]:::layer
    end

    subgraph 渲染层["渲染层"]
        R1["SanitizePlugin<br/>HTML 标签白名单"]:::layer
        R2["escapeHtml<br/>输出编码"]:::layer
        R3["sanitizeUrl<br/>协议白名单"]:::layer
    end

    subgraph 存储层["存储层"]
        S1["localStorage<br/>Token · env · debug · 标签排序"]:::layer
        S2["内存缓存<br/>API 响应 · 模板"]:::layer
        S3["sessionStorage<br/>未使用"]:::layer
    end

    输入层 --> 传输层 --> 渲染层 --> 存储层

    classDef layer fill:#e3f2fd,stroke:#1565c0;
```

### 5.2 安全措施汇总

| 层面 | 措施 | 实现 |
|------|------|------|
| 输入验证 | URL 参数仅支持已知 key；搜索词无限制但渲染前净化 | `config.js` + `SanitizePlugin` |
| 认证 | Token 经 X-Token 头传递；401 自动清除并重新输入 | `authUtils.js` + `authErrorHandler.js` |
| 传输安全 | credentials: 'omit'；CORS 模式 | `requestHelper.js` |
| 输出编码 | HTML 净化（白名单标签）；URL 协议白名单（http/https/mailto） | `SanitizePlugin` + `sanitizeUrl()` |
| 存储安全 | Token 仅 localStorage；敏感操作前验证 Token 有效性 | `authUtils.js` |

**关键约束**: Token 和 webhook URL 禁止写入源码或文档（P0 安全规则）

---

## §6 性能策略

| 策略 | 实现 | 效果 |
|------|------|------|
| 零构建 | 无编译/打包，浏览器原生加载 ESM | 消除构建时间，首屏加载 = 网络 + 解析 |
| CDN 缓存 | 第三方库（Vue、marked、mermaid）CDN 加载 | 利用浏览器缓存 + CDN 边缘节点 |
| 模板缓存 | HTML 模板内存 + localStorage 缓存 | 组件二次加载瞬间完成 |
| API 缓存 | 内存缓存 5min TTL，100 项限制 | 减少重复请求，降低 API 压力 |
| 防抖节流 | 搜索输入 300ms 防抖；滚动事件节流 | 减少不必要的计算和渲染 |
| 懒加载 | 非首屏组件按需加载 | 减少初始 JS 解析量 |
| GPU 加速 | CSS transform3d + will-change + backface-visibility | 动画 60fps |
| 减少动画 | prefers-reduced-motion 时将动画时长设为 0ms | 无障碍 + 性能双赢 |

---

## §7 项目约束验证

| # | 约束 | 验证方式 | 状态 |
|---|------|---------|:---:|
| 1 | 零构建链 — 无 transpile/bundle/dev server | 检查项目无 package.json、无构建配置 | ✅ |
| 2 | 无外部包管理 — 无 npm 依赖 | 检查无 node_modules、无 package.json | ✅ |
| 3 | 浏览器安全 — credentials: 'omit' | 全局搜索 fetch 调用 | ✅ |
| 4 | 视图隔离 — 每个视图自包含 | 检查 src/views/ 目录结构 | ✅ |
| 5 | 配置即环境 — local/prod 切换 | config.js 仅两环境 | ✅ |
| 6 | 状态变更走 store — 不跨组件改 ref | 代码审查 | ✅ |
| 7 | 统一日志 — logInfo/logWarn/logError | 全局搜索 console.log | ✅ |

---

## §8 跨文档索引

| 方向 | 文档 |
|------|------|
| ↑ 问题空间基线 | [YiWeb-01-故事任务](./YiWeb-01-故事任务.md) — §1 Story 1–6, §2 FP 1–10, §4 风险 |
| ↑ 用户空间基线 | [YiWeb-02-用户使用场景](./YiWeb-02-用户使用场景.md) — §2 体验基线 |
| ↓ 验证 | [YiWeb-05-测试用例评审](./YiWeb-05-测试用例评审.md) — 用例关联架构方案 |

---

> **变更记录**: v1.0 初始基线 — 7 章架构评审：视图框架、状态管理、API 通信、Markdown 管道、安全架构、性能策略、项目约束
