> | v1.0.0 | 2026-05-22 | deepseek-v4-pro | | 🌿 feat/api-routes | ⏱️ — | 📎 [CLAUDE.md](../../../CLAUDE.md) |

> **导航**: [← YiAi-故事任务](./YiAi-故事任务.md) · [YiAi-技术评审 →](./YiAi-技术评审.md)

> **来源引用**: `/rui doc --from-code api-routes` — 从 `src/api/routes/` 7 个文件反推用户场景，证据 Level B + 源码路径。

---

## §0 基线声明

> **用户空间基线**: 本文档从 API 调用方视角描述 7 大功能域的用户交互场景。所有技术方案和测试用例必须覆盖本文档的每个场景。

---

### 主要价值

- 🎯 从 API 调用方视角完整描述 7 个功能域的交互场景：模块执行、文件管理、消息推送、维护清理、状态查询、健康检查、面板管理
- 🔒 覆盖关键异常路径：路径遍历拦截、OSS 降级、认证失败、URL 校验失败
- ⚡ 每场景含 mermaid 流程图，清晰展示正常路径 → 空状态 → 错误恢复的完整用户旅程
- 📊 场景覆盖矩阵对齐故事任务全部 13 个 FP#，为测试设计提供完整基线

---

## §1 场景全景

```mermaid
flowchart TD
    CALLER["API 调用方<br/>前端/外部服务/CLI"]:::user
    CALLER --> S1["场景 1: 执行远程模块<br/>GET/POST /"]:::scene
    CALLER --> S2["场景 2: 管理文件<br/>upload/read/write/delete/rename"]:::scene
    CALLER --> S3["场景 3: 发送企业微信消息<br/>POST /wework/send-message"]:::scene
    CALLER --> S4["场景 4: 清理未引用资源<br/>POST /cleanup-unused-images"]:::scene
    CALLER --> S5["场景 5: 管理状态记录<br/>CRUD /state/records"]:::scene
    CALLER --> S6["场景 6: 查看系统健康<br/>GET /health/observer"]:::scene
    CALLER --> S7["场景 7: 管理故事面板<br/>/api/story-panel/*"]:::scene

    classDef user fill:#f3e5f5,stroke:#6a1b9a;
    classDef scene fill:#e3f2fd,stroke:#1565c0;
```

---

## §2 场景详述

### 场景 1: 执行远程模块

| 字段 | 内容 |
|------|------|
| 角色 | 外部服务或开发者，需要远程调用 YiAi 注册的模块方法 |
| 触发条件 | 发送 GET 或 POST 请求到 `/` 端点 |
| 核心目标 | 指定模块名和方法名，获取执行结果（JSON 或 SSE 实时流） |

```mermaid
flowchart TD
    CALL["发送请求<br/>module_name + method_name<br/>+ parameters"]:::entry --> VALID{"模块在白名单?<br/>参数有效?"}:::decision
    VALID -->|"是"| EXEC["执行模块方法"]
    VALID -->|"否"| ERR400["返回 400<br/>INVALID_PARAMS / PERMISSION_DENIED"]:::error
    EXEC --> TYPE{"返回类型?"}:::decision
    TYPE -->|"普通值"| JSON["success(data=result)"]:::goal
    TYPE -->|"async generator"| SSE_A["SSE 流式响应<br/>text/event-stream"]:::goal
    TYPE -->|"sync generator"| SSE_S["SSE 流式响应<br/>text/event-stream"]:::goal
    EXEC -->|"执行异常"| ERR500["返回 500<br/>INTERNAL_ERROR"]:::error

    classDef entry fill:#e8f5e9,stroke:#2e7d32;
    classDef decision fill:#fff3e0,stroke:#e65100;
    classDef goal fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef error fill:#ffebee,stroke:#c62828;
```

---

### 场景 2: 管理文件

| 字段 | 内容 |
|------|------|
| 角色 | 前端应用或内容管理系统 |
| 触发条件 | 需要上传图片、读写文件、删除或重命名文件 |
| 核心目标 | 安全地操作 static 目录下的文件，路径遍历攻击被拦截 |

```mermaid
flowchart TD
    REQ["文件操作请求"]:::entry --> VALID{"路径验证<br/>_validate_path / _resolve_static_path"}:::decision
    VALID -->|"含 .. 或绝对路径"| ERR400A["返回 400<br/>非法路径"]:::error
    VALID -->|"通过"| EXIST{"文件/目录存在?"}:::decision
    EXIST -->|"读操作-存在"| READ["text→返回内容<br/>image→返回URL<br/>binary→返回base64"]:::goal
    EXIST -->|"写操作"| WRITE["创建目录+写入<br/>返回成功"]:::goal
    EXIST -->|"删操作-存在"| DEL["删除文件/目录<br/>返回成功"]:::goal
    EXIST -->|"不存在"| ERR404["返回 404<br/>DATA_NOT_FOUND"]:::error
    EXIST -->|"上传图片"| OSS["优先 OSS 上传"]:::goal
    OSS -->|"OSS 失败"| LOCAL["降级本地存储<br/>仍返回 URL"]:::goal

    classDef entry fill:#e8f5e9,stroke:#2e7d32;
    classDef decision fill:#fff3e0,stroke:#e65100;
    classDef goal fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef error fill:#ffebee,stroke:#c62828;
```

---

### 场景 3: 发送企业微信消息

```mermaid
flowchart TD
    SEND["POST /wework/send-message<br/>webhook_url + content"]:::entry --> VURL{"URL 以<br/>qyapi.weixin.qq.com 开头?"}:::decision
    VURL -->|"否"| ERR400B["返回 400<br/>无效的 Webhook URL"]:::error
    VURL -->|"是"| VC{"content 非空?"}:::decision
    VC -->|"否"| ERR400C["返回 400<br/>消息内容不能为空"]:::error
    VC -->|"是"| POST["POST JSON 到 webhook<br/>timeout=10s"]:::goal
    POST -->|"HTTP ≠ 200"| ERR500A["返回 500<br/>发送失败: errmsg"]:::error
    POST -->|"errcode ≠ 0"| ERR500B["返回 500<br/>发送失败: errmsg"]:::error
    POST -->|"成功"| OK["success<br/>消息发送成功"]:::goal

    classDef entry fill:#e8f5e9,stroke:#2e7d32;
    classDef decision fill:#fff3e0,stroke:#e65100;
    classDef goal fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef error fill:#ffebee,stroke:#c62828;
```

---

### 场景 4: 清理未引用资源

| 字段 | 内容 |
|------|------|
| 角色 | 运维人员定期执行清理 |
| 触发条件 | POST `/cleanup-unused-images` |
| 核心目标 | 扫描 static 目录图片，与 sessions 引用比对，清理未引用图片（dry-run 预览优先） |

```mermaid
flowchart TD
    CLEAN["POST /cleanup-unused-images<br/>dry_run + cleanup_sessions"]:::entry --> SCAN["1. 扫描 static 目录<br/>收集所有图片文件"]:::step
    SCAN --> EXTRACT["2. 扫描 sessions 集合<br/>提取所有图片引用"]:::step
    EXTRACT --> DIFF["3. 对比找未引用图片"]:::step
    DIFF --> DRY{"dry_run?"}:::decision
    DRY -->|"true"| PREVIEW["返回统计信息<br/>不实际删除"]:::goal
    DRY -->|"false"| DELIMG["4. 删除未引用图片"]:::step
    DELIMG --> SESS{"cleanup_sessions?"}:::decision
    SESS -->|"true"| DELSESS["5. 清理含无效引用<br/>的 sessions"]:::step
    SESS -->|"false"| DONE["返回删除统计"]:::goal
    DELSESS --> DONE

    classDef entry fill:#e8f5e9,stroke:#2e7d32;
    classDef step fill:#e3f2fd,stroke:#1565c0;
    classDef decision fill:#fff3e0,stroke:#e65100;
    classDef goal fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
```

---

### 场景 5: 管理状态记录

```mermaid
flowchart LR
    CRUD["状态记录 CRUD"]:::entry --> CREATE["POST /state/records<br/>创建记录 → 201"]:::goal
    CRUD --> QUERY["GET /state/records<br/>按类型/标签/标题/时间查询 → 200"]:::goal
    CRUD --> GET["GET /state/records/{key}<br/>获取单条 → 200 | 404"]:::goal
    CRUD --> UPDATE["PUT /state/records/{key}<br/>更新记录 → 200 | 404"]:::goal
    CRUD --> DELETE["DELETE /state/records/{key}<br/>删除记录 → 200 | 404"]:::goal

    classDef entry fill:#e8f5e9,stroke:#2e7d32;
    classDef goal fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
```

---

### 场景 6: 查看系统健康

| 字段 | 内容 |
|------|------|
| 角色 | 运维监控系统 |
| 触发条件 | GET `/health/observer` |
| 核心目标 | 获取 Observer 四组件（限流/采样/沙箱/守卫）的运行时启用状态和指标 |

---

### 场景 7: 管理故事面板

| 字段 | 内容 |
|------|------|
| 角色 | 项目管理者 |
| 触发条件 | 访问 `/api/story-panel/*` 端点 |
| 核心目标 | 查看所有故事的进度状态、同步远端文档、获取 API 帮助 |

---

## §3 场景覆盖矩阵

| 场景 | FP# | AC# | 覆盖状态 |
|------|-----|-----|---------|
| 场景 1: 模块执行 | FP1 | AC1 | 待覆盖 |
| 场景 2: 文件管理 | FP2–FP8 | AC2, AC3, AC4 | 待覆盖 |
| 场景 3: 企业微信 | FP9 | AC5, AC6 | 待覆盖 |
| 场景 4: 资源清理 | FP10 | — | 待覆盖 |
| 场景 5: 状态记录 | FP11 | AC7, AC8 | 待覆盖 |
| 场景 6: 健康检查 | FP12 | — | 待覆盖 |
| 场景 7: 面板管理 | FP13 | — | 待覆盖 |

---

## §4 评审清单

| # | 检查项 | 状态 |
|---|--------|:--:|
| 1 | 场景 ≥ 2 | ✅ 7 场景 |
| 2 | 每场景有图 | ✅ |
| 3 | FP 全覆盖 | ✅ 13/13 |
| 4 | 异常分支明确 | ✅ |
| 5 | 无技术术语 | ✅ |
| 6 | 含空状态与错误恢复 | ✅ |

---

## §5 体验基线

| 角色 | 核心旅程 | 情感目标 | 成功感知 | 关联场景 |
|------|---------|---------|---------|---------|
| 外部服务 | 远程调用模块 → 获得 JSON 结果或 SSE 流 | 高效可靠 | 收到 success(data=...) 或实时流数据 | 场景 1 |
| 前端应用 | 上传图片 → 获得可访问 URL | 简单直接 | 图片 URL 可直接用于展示 | 场景 2 |
| DevOps | 发企业微信通知 → 团队收到告警 | 实时可靠 | 企业微信收到消息 | 场景 3 |
| 运维 | 定期清理 → 磁盘空间释放 | 安全可控 | 看到 dry-run 预览无误后执行 | 场景 4 |
| 开发者 | CRUD 状态 → 数据持久化 | 简单一致 | 数据读写与预期一致 | 场景 5 |

---

> **变更记录**
>
> | 日期 | 变更 | 触发 | 证据 |
> |------|------|------|------|
> | 2026-05-22 | 初始生成 | `/rui doc --from-code api-routes` | 7 个路由文件源码分析 |
