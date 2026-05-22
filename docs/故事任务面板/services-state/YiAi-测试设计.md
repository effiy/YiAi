# YiAi-测试设计 — services-state

> 结构化状态存储子系统测试设计。3 组件 20 用例。
>
> **来源**：源码分析 | **证据等级**：B | **项目类型**：backend

---

## 测试用例

### TC1–TC8: StateStoreService

| TC# | 场景 | 预期 |
|-----|------|------|
| TC1 | 创建记录（无 key） | 自动生成 UUID key，含 created_time/updated_time |
| TC2 | 创建记录（指定 key） | 使用指定 key，不覆盖 |
| TC3 | 按 record_type 查询 | 仅返回匹配类型的记录 |
| TC4 | 按 tags 查询 | $in 匹配，命中任一标签即返回 |
| TC5 | 按 title_contains 查询 | 模糊匹配，大小写不敏感 |
| TC6 | 按时间范围查询 | created_after/created_before 过滤正确 |
| TC7 | 分页查询 | total/totalPages 正确，page_size 受 max_limit 约束 |
| TC8 | 查询空结果 | 返回空 list + total=0 |

### TC9–TC12: StateStoreService 单条操作

| TC# | 场景 | 预期 |
|-----|------|------|
| TC9 | get 存在的 key | 返回完整记录 |
| TC10 | get 不存在的 key | 返回 None |
| TC11 | update 存在的 key | updated_time 更新，key/created_time 不变 |
| TC12 | delete 不存在的 key | ValueError("Record not found") |

### TC13–TC16: SkillRecorder

| TC# | 场景 | 预期 |
|-----|------|------|
| TC13 | 同步记录成功 | state_service.create 被调用，参数正确 |
| TC14 | 记录失败容错 | 内部异常 → logger.error，不抛出 |
| TC15 | fire-and-forget | record_async 立即返回，create_task 被调度 |
| TC16 | 全局单例 | get_recorder() 两次返回同一实例 |

### TC17–TC20: SessionAdapter

| TC# | 场景 | 预期 |
|-----|------|------|
| TC17 | 标准文档适配 | 字段正确映射，返回 SessionState |
| TC18 | 非标准字段处理 | 未知字段归入 metadata |
| TC19 | 验证失败宽松回退 | model_validate 失败 → 仍返回 SessionState |
| TC20 | 批量适配统计 | 返回正确的 success_count/failure_count/errors |

---

## Gate A 交接信号

| 检查项 | 状态 |
|--------|:---:|
| AC 全覆盖 (AC1–AC4) | ✓ |
| 创建/查询/更新/删除 CRUD 测试 | ✓ (TC1–TC12) |
| SkillRecorder 容错测试 | ✓ (TC14) |
| SessionAdapter 字段映射 + 回退测试 | ✓ (TC17–TC19) |

---

### 主要价值

- ✅ **20 用例覆盖 3 组件**
- 🛡️ **容错路径充分** — 记录失败/适配失败/空结果均有覆盖
- 🔍 **查询维度完整** — 5 种过滤条件 + 分页
- 📝 **状态覆盖** — 创建/查询/更新/删除 + 边界（不存在/空结果）

---

## 回溯链

| 来源 | 路径 |
|------|------|
| 故事任务 | `YiAi-故事任务.md` §5 |
| 源码 | `src/services/state/` |

### 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2026-05-22 | 1.0.0 | 初始 /rui doc --from-code |
