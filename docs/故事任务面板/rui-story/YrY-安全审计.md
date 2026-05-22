> | v1.4.8 | 2026-05-20 | deepseek-v4-pro | 🌿 feat/rui-story | ⏱️ — | 📎 [CLAUDE.md](../../../CLAUDE.md) |

> **导航**: [← YrY-技术评审](./YrY-技术评审.md) · [← YrY-测试设计](./YrY-测试设计.md) · [YrY-实施报告 →](./YrY-实施报告.md)

> **来源引用**: 从 `skills/rui-story/rui-story.mjs` 源码 + `skills/rui-story/SKILL.md` 操作边界反推。证据 Level B + 源码路径。独立安全审计，不依赖 coder 自评。

[§0 基线溯源](#sec0-baseline) · [§1 资产识别](#sec1-assets) · [§2 威胁建模](#sec2-threats) · [§3 信任边界](#sec3-trust) · [§4 缓解措施](#sec4-mitigations) · [§5 合规检查](#sec5-compliance) · [§6 评审清单](#sec6-checklist)

---

### 主要价值

- 🎯 识别 8 个威胁面 — 覆盖命令注入/路径遍历/Token 泄露/未授权访问
- 🔒 信任边界闭合 — CLI↔Shell、用户输入↔文件系统、CLI↔API 三边界
- ⚡ P0 威胁全部有缓解 — Token 不落盘、kebab-case 约束、确认机制
- 📊 合规 6 项全覆盖 — 认证/密钥/输入校验/最小权限/默认拒绝/审计日志

---

<a id="sec0-baseline"></a>

## §0 基线溯源

| 审计条目 | 覆盖技术评审章节 | 覆盖故事任务 FP# | 覆盖使用场景 | 审计结论 |
|---------|----------------|-----------------|------------|---------|
| Token 安全管理 | §2.3, §7.#1 | R1 | 全部查询场景 | 通过 — 环境变量注入，不落盘 |
| 命令注入防护 | §7.#2 | R3 | — | 通过 — kebab-case 约束 |
| 路径遍历防护 | §7.#3 | R5, R6, R7 | 场景 E, F | 通过 — name 格式约束 |
| 未授权访问 | §2.3, §7.#4 | R1 | 全部查询场景 | 通过 — X-Token + HTTPS |
| 破坏性操作防护 | §7.#5 | R5, R6, R7 | 场景 E, F | 通过 — 确认机制 |
| 信息泄露 | §7.#6 | R1 | 全部场景 | 通过 — 错误截断 |
| 输入校验 | §4.1 parseArgs | R2 | 全部场景 | 通过 — 白名单命令路由 |

---

<a id="sec1-assets"></a>

## §1 资产识别

### 1.1 数据资产

| 资产 | 敏感级别 | 存储位置 | 访问路径 |
|------|---------|---------|---------|
| API_X_TOKEN | 高 — 远端 API 认证凭据 | 环境变量（进程内存） | process.env.API_X_TOKEN |
| 远端 sessions 数据 | 中 — 故事文档内容 | 远端 API (api.effiy.cn) | POST / query_documents |
| CLAUDE.md 项目名 | 低 — 项目标识 | 本地文件系统 | fs.readFileSync |
| .memory/rui-state.json | 低 — 管线阻断状态 | 本地文件系统 | fs.readFileSync |

### 1.2 功能资产

| 端点/组件 | 认证要求 | 授权级别 |
|----------|---------|---------|
| POST api.effiy.cn/ (query_documents) | X-Token | 读取 sessions 集合 |
| POST api.effiy.cn/read-file | X-Token | 读取单个文件内容 |
| git branch --list | 无（本地） | 读取本地 git 分支信息 |
| 本地文件系统读取 | 无（OS 权限） | 读取 CLAUDE.md, rui-state.json |
| 本地文件系统写入 (clear/remove) | 无（OS 权限） | 删除 docs/故事任务面板/ 下文件 |

---

<a id="sec2-threats"></a>

## §2 威胁建模

| # | 威胁 | 攻击面 | 可能性 | 影响 | STRIDE 分类 |
|---|------|--------|--------|------|------------|
| T1 | 恶意故事名导致命令注入 via git | CLI args → execSync | L | H | 权限提升 |
| T2 | 路径遍历读取/删除任意文件 | CLI args → 文件系统 | L | H | 篡改 |
| T3 | API_X_TOKEN 泄露到 stdout/stderr/日志 | 进程内存 → I/O 流 | M | H | 信息泄露 |
| T4 | 未授权用户查询远端 API | 无 Token → API | M | M | 信息泄露 |
| T5 | 中间人攻击截获 API 通信 | 网络传输 | L | H | 信息泄露 |
| T6 | clear/remove 误操作导致文档丢失 | 用户确认 → 文件系统 | M | M | 篡改 |
| T7 | 远端 API 响应注入恶意内容到 stdout | API 响应 → stdout | L | M | 篡改 |
| T8 | 拒绝服务 — 大量并发请求耗尽连接 | 并发 worker → API | L | M | 拒绝服务 |

---

<a id="sec3-trust"></a>

## §3 信任边界

| 边界 | 跨越方向 | 数据流 | 校验点 | 当前状态 |
|------|---------|--------|--------|---------|
| 用户输入 → CLI 进程 | 入站 | CLI args (process.argv) | parseArgs() 白名单路由 + kebab-case 约束 | 已加固 |
| CLI 进程 → Shell (git) | 出站 | git branch --list 命令 | 硬编码命令模板，storyName 来自受控解析 | 已加固 |
| CLI 进程 → 本地文件系统 | 出站 | fs.readFileSync 路径 | 路径拼接自受控的 projectRoot + storyName | 已加固 |
| CLI 进程 → API (网络) | 出站 | HTTPS POST + X-Token | fetchJson() 自动注入 Token，30s 超时 | 已加固 |
| API → CLI 进程 (网络) | 入站 | HTTPS 响应 | JSON.parse 防御性解析 `data?.data?.list \|\| []` | 已加固 |
| CLI 进程 → stdout/stderr | 出站 | 格式化输出 | Token 不输出；错误信息截断至 500 字符 | 已加固 |

---

<a id="sec4-mitigations"></a>

## §4 缓解措施

| 威胁# | 缓解措施 | 实现位置 | 优先级 | 状态 |
|-------|---------|---------|--------|------|
| T1 | kebab-case 约束 `^[a-z0-9]+(-[a-z0-9]+)*$`；git 命令硬编码模板 | SKILL.md 命名规范 + checkGitBranch() | P0 | 已实施 |
| T2 | name 格式约束不含 `../` 或 `/`；路径拼接使用 path.join | parseArgs() + extractStoryName() | P0 | 已实施 |
| T3 | API_X_TOKEN 仅在 fetchJson() 中使用；console.log 不输出 Token；错误信息不含请求头 | fetchJson() + 全局纪律 | P0 | 已实施 |
| T4 | API_X_TOKEN 缺失时优雅退出 + 配置指引，不尝试无认证请求 | main() needsRemote 检查 | P0 | 已实施 |
| T5 | HTTPS 协议 enforced（API_URL 默认 https://）；fetch 使用 TLS | fetchJson() | P0 | 已实施 |
| T6 | clear/remove 先展示双重清单，用户确认后执行；不可跳过确认 | SKILL.md clear/remove 流程 | P0 | 已实施 |
| T7 | 响应内容仅格式化输出，不做 eval/执行；错误截断 500 字符 | fetchJson() `text.slice(0, 500)` | P1 | 已实施 |
| T8 | 并发限制 CONCURRENCY=4；HTTP_TIMEOUT=30s；AbortController | inferTypesBatch() + fetchJson() | P1 | 已实施 |

---

<a id="sec5-compliance"></a>

## §5 合规检查

| # | 检查项 | 要求 | 当前状态 | 偏差说明 |
|---|--------|------|---------|---------|
| 1 | 认证不可绕过 | 所有 API 请求必须携带有效 Token | ✅ API_X_TOKEN 缺失时阻止查询 | — |
| 2 | 密钥不落盘 | Token 不出现在源码、配置文件、日志 | ✅ 仅通过环境变量传入 | — |
| 3 | 输入必校验 | 用户输入经白名单路由 + 格式约束 | ✅ parseArgs() 白名单 + kebab-case | — |
| 4 | 最小权限 | 只读命令不写文件系统 | ✅ overview/list/show/recommend/health 无 fs write | — |
| 5 | 默认拒绝 | 未知命令拒绝执行 | ✅ parseArgs() 未知命令 exit(0) + 提示 | — |
| 6 | 审计日志完整 | 操作有追踪 | ⚠️ 命令行操作无审计日志 | clear/remove 由 agent 执行，SKILL.md 流程含确认记录 |

---

<a id="sec6-checklist"></a>

## §6 评审清单

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | P0 威胁全部缓解 | ✅ T1–T6 已实施 |
| 2 | 信任边界闭合 | ✅ 6 个边界均标注状态 |
| 3 | 密钥无硬编码 | ✅ 源码中无 Token/密钥 |
| 4 | 输入校验完整 | ✅ 白名单 + 格式约束 |
| 5 | 认证链路闭环 | ✅ Token 缺失时阻止查询 |
| 6 | 审计日志可达 | ⚠️ 命令行操作缺审计日志 — 由 agent 执行时 SKILL.md 流程含确认记录 |
| 7 | 合规检查通过 | ✅ 5/6 通过，1 项标注偏差 |

---

> **变更记录**
>
> | 日期 | 变更 | 触发 | 证据 |
> |------|------|------|------|
> | 2026-05-20 | 初始生成 | doc --from-code rui-story | skills/rui-story/rui-story.mjs + SKILL.md |
