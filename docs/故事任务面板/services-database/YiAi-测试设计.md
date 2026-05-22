# YiAi-测试设计 — services-database

> 数据服务层的测试设计文档。覆盖 `data_service.py` 全部 7 个公共方法 + `mongo_store.py` 差异点。
>
> **来源**：源码分析 `/rui doc --from-code services-database`
> **证据等级**：B（只读源码 + 静态分析）
> **项目类型**：backend

---

## 效果示意

```mermaid
flowchart LR
    STORY["故事任务 AC#"]:::story --> TC["测试用例"]:::test
    TC --> GATE_A["Gate A<br/>测试先行验证"]:::gate
    GATE_A -->|"通过"| IMPL["进入实现阶段"]

    classDef story fill:#fff3e0,stroke:#e65100;
    classDef test fill:#e3f2fd,stroke:#1565c0;
    classDef gate fill:#e8f5e9,stroke:#2e7d32;
```

---

## 测试范围

| 维度 | 范围 | 排除 |
|------|------|------|
| 方法 | 7 个公共方法（data_service）+ mongo_store 差异点 | 私有 helper 函数（通过公共方法间接覆盖） |
| 集合 | rss / sessions / 通用集合 | 集合的创建/删除（运维层面） |
| 边界 | 参数验证、异常路径、并发竞态 | 数据库宕机（基础设施层面） |

---

## 测试用例

### TC1: query_documents — 基本分页查询

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP1, FP2 |
| 前置条件 | rss 集合中有 ≥50 条测试数据 |
| 输入 | `collection_name='rss', pageNum=1, pageSize=10` |
| 预期 | 返回 `{list: [10条], total: ≥50, pageNum: 1, pageSize: 10, totalPages: ≥5}` |
| 验证点 | list 长度=10；每条含 key 字段；total 正确 |

### TC2: query_documents — 字段投影（fields 白名单）

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP2 |
| 前置条件 | rss 集合中有测试数据 |
| 输入 | `collection_name='rss', fields='title,link', pageSize=5` |
| 预期 | 返回文档仅含 title、link、key 三个字段 |
| 验证点 | 返回文档不含 pubDate/description 等非指定字段；key 字段自动保留 |

### TC3: query_documents — 字段投影（excludeFields 黑名单）

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP2 |
| 前置条件 | rss 集合中有测试数据 |
| 输入 | `collection_name='rss', excludeFields='description,content'` |
| 预期 | 返回文档不含 description 和 content |
| 验证点 | 排除字段不在返回文档中；非排除字段正常返回 |

### TC4: query_documents — 字符串模糊搜索（单关键词）

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC6 |
| 关联 FP# | FP4 |
| 前置条件 | rss 集合中有 title='Python异步编程指南' 的文档 |
| 输入 | `collection_name='rss', title='Python'` |
| 预期 | 返回 title 包含 "Python" 的文档 |
| 验证点 | 目标文档在结果中；大小写不敏感匹配；正则特殊字符被转义 |

### TC5: query_documents — 多关键词 OR 搜索

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP4 |
| 前置条件 | rss 集合中有 title 含 "Python" 和 title 含 "FastAPI" 的文档 |
| 输入 | `collection_name='rss', title='Python,FastAPI'` |
| 预期 | 返回 title 含 "Python" 或 "FastAPI" 的文档（$or 逻辑） |
| 验证点 | 两种文档均在结果中；无重复 |

### TC6: query_documents — NoSQL 注入防护验证

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC6 |
| 关联 FP# | FP4 |
| 前置条件 | 任意集合 |
| 输入 | `collection_name='rss', title='test.*$('` |
| 预期 | re.escape 转义为字面量匹配，不触发正则注入 |
| 验证点 | 搜索行为等同于搜索字面量字符串 "test.*$("；不影响查询结构 |

### TC7: query_documents — 日期范围过滤（isoDate 范围）

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP3 |
| 前置条件 | rss 集合中有 pubDate 为 '2026-05-15' 和 '2026-05-20' 的文档 |
| 输入 | `collection_name='rss', isoDate='2026-05-15,2026-05-18'` |
| 预期 | 返回 pubDate 在 2026-05-15 ~ 2026-05-18 之间的文档 |
| 验证点 | 2026-05-15 文档在结果中；2026-05-20 不在；多日期格式匹配 |

### TC8: query_documents — 日期范围过滤（单日 isoDate）

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP3 |
| 前置条件 | rss 集合中有 pubDate='2026-05-15' 的文档 |
| 输入 | `collection_name='rss', isoDate='2026-05-15'` |
| 预期 | 返回该日期的文档 |
| 验证点 | 单日等同于范围 [date, date] |

### TC9: query_documents — 数值区间过滤

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP1 |
| 前置条件 | 集合中有 price 字段数据：10, 50, 100 |
| 输入 | `collection_name='products', price=[20, 80]`（2元素数组） |
| 预期 | 返回 20 ≤ price < 80 的文档 |
| 验证点 | price=50 在结果中；price=10 和 100 不在 |

### TC10: query_documents — $in 列表过滤

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP1 |
| 前置条件 | 集合中有 category 为 A/B/C 的文档 |
| 输入 | `collection_name='rss', category=['A', 'B', 'D']`（>2元素数组） |
| 预期 | 返回 category ∈ {A, B, D} 的文档 |
| 验证点 | $in 语义正确；D 无匹配不影响结果 |

### TC11: query_documents — key 精确匹配

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP1 |
| 前置条件 | 已知某文档 key |
| 输入 | `collection_name='rss', key='已知key值'` |
| 预期 | 仅返回 key 精确匹配的文档 |
| 验证点 | 不走模糊搜索；大小写敏感 |

### TC12: query_documents — sessions 自动排除 pageContent

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP10 |
| 前置条件 | sessions 集合中有含 pageContent 的文档 |
| 输入 | `collection_name='sessions'`（不传 fields） |
| 预期 | 返回文档不含 pageContent 字段 |
| 验证点 | 默认投影 `{pageContent: 0}` 生效 |

### TC13: query_documents — sessions fields 白名单中过滤 pageContent

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP10 |
| 前置条件 | sessions 集合有文档 |
| 输入 | `collection_name='sessions', fields='title,pageContent'` |
| 预期 | pageContent 被从 fields 列表中移除 |
| 验证点 | 返回字段不含 pageContent |

### TC14: query_documents — 分页边界值

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP1 |
| 前置条件 | 集合中有 ≥8000 条数据 |
| 输入 | `pageSize=10000` |
| 预期 | pageSize 被限制为 8000 |
| 验证点 | `min(8000, ...)` 生效 |

### TC15: query_documents — 无效分页参数

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP1 |
| 前置条件 | 任意集合 |
| 输入 | `pageSize='abc'`（非数字） |
| 预期 | 抛出 ValueError("分页参数必须是有效的整数") |
| 验证点 | 异常消息正确 |

### TC16: create_document — 基本创建

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC2 |
| 关联 FP# | FP5 |
| 前置条件 | rss 集合存在 |
| 输入 | `collection_name='rss', data={title: '测试', link: 'https://test.com/1'}` |
| 预期 | 返回 `{key: <uuid>}`；数据入库存 |
| 验证点 | key 为 UUID v4 格式；createdTime/updatedTime 已生成；order 自动分配 |

### TC17: create_document — data 为空时使用 params 其余字段

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC2 |
| 关联 FP# | FP5 |
| 前置条件 | rss 集合存在 |
| 输入 | `collection_name='rss', title='测试', link='https://test.com/2'`（不传 data） |
| 预期 | params 中除 cname/collection_name 外的字段合并为 data |
| 验证点 | 文档正常创建，title/link 正确 |

### TC18: create_document — RSS link 重复阻断

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC5 |
| 关联 FP# | FP9 |
| 前置条件 | rss 集合已有 link='https://dup.com' |
| 输入 | `collection_name='rss', data={link: 'https://dup.com'}` |
| 预期 | 抛出 ValueError("link 字段值 'https://dup.com' 已存在，不能重复创建") |
| 验证点 | 重复创建被阻断；错误消息包含 link 值 |

### TC19: create_document — 空数据阻断

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC2 |
| 关联 FP# | FP5 |
| 前置条件 | 任意集合 |
| 输入 | `collection_name='rss'`（无 data 且无其他字段） |
| 预期 | 抛出 ValueError("创建数据不能为空") |
| 验证点 | 空数据不写入数据库 |

### TC20: get_document_detail — 查询存在文档

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP5 |
| 前置条件 | 已知某文档 key |
| 输入 | `collection_name='rss', id='已知key'` |
| 预期 | 返回完整文档（不含 _id） |
| 验证点 | 文档字段正确；sessions 排除 pageContent |

### TC21: get_document_detail — 查询不存在文档

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP5 |
| 前置条件 | 任意集合 |
| 输入 | `collection_name='rss', id='nonexistent-key'` |
| 预期 | 抛出 ValueError("未找到ID为 nonexistent-key 的数据") |
| 验证点 | 异常消息包含 key 值 |

### TC22: update_document — 基本更新

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC3 |
| 关联 FP# | FP6 |
| 前置条件 | rss 集合有 key=xxx 的文档 |
| 输入 | `collection_name='rss', data={key: 'xxx', title: '更新后的标题'}` |
| 预期 | 返回 `{key: 'xxx', updated: true}` |
| 验证点 | title 已更新；updatedTime 已刷新；key/createdTime 未变 |

### TC23: update_document — 受保护字段不可修改

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC3 |
| 关联 FP# | FP6 |
| 前置条件 | 已知文档 key |
| 输入 | data 含 `key, _id, createdTime` 的新值 |
| 预期 | _id、key、createdTime 被 pop 移除，不会更新 |
| 验证点 | 文档的 _id/key/createdTime 保持不变 |

### TC24: update_document — 不存在的 key

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC3 |
| 关联 FP# | FP6 |
| 前置条件 | 无 |
| 输入 | `collection_name='rss', data={key: '不存在的key'}` |
| 预期 | 抛出 ValueError("未找到ID为 不存在的key 的数据") |
| 验证点 | 不存在时不产生副作用 |

### TC25: update_document — mongo_store link-based 更新

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC3 |
| 关联 FP# | FP6, FP12 |
| 前置条件 | rss 集合有 link='https://existing.com' 的文档 |
| 输入 | `mongo_store.update_document('rss', {link: 'https://existing.com', title: 'new'})` |
| 预期 | 按 link 匹配更新成功；contentHash 自动生成 |
| 验证点 | contentHash 字段被写入；find_one_and_update 返回更新后文档 |

### TC26: update_document — mongo_store link 冲突检测

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC5 |
| 关联 FP# | FP9, FP12 |
| 前置条件 | rss 有 key=A link=LA 和 key=B link=LB |
| 输入 | 更新 key=A 的 link 为 LB |
| 预期 | 抛出 ValueError("link 字段值 'LB' 已被其他记录使用") |
| 验证点 | 跨文档 link 冲突被阻断 |

### TC27: upsert_document — 更新已存在文档

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC8 |
| 关联 FP# | FP7 |
| 前置条件 | 已知文档 key |
| 输入 | `filter={key: 'xxx'}, update={$set: {title: 'new'}}` |
| 预期 | matched_count=1, upserted_id=null |
| 验证点 | 文档被更新而非新建 |

### TC28: upsert_document — 插入不存在文档

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC8 |
| 关联 FP# | FP7 |
| 前置条件 | 无 |
| 输入 | `filter={key: 'new-key'}, update={$set: {title: 'new'}}` |
| 预期 | upserted_id 非空；自动生成 key/createdTime/updatedTime |
| 验证点 | $setOnInsert 生效 |

### TC29: delete_document — 基本删除

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC4 |
| 关联 FP# | FP8 |
| 前置条件 | rss 有 key=xxx 的文档 |
| 输入 | `collection_name='rss', key='xxx'` |
| 预期 | 返回 `{key: 'xxx', deleted: true}` |
| 验证点 | 再次查询该 key 返回空；count 减少 1 |

### TC30: delete_document — 删除不存在文档

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC4 |
| 关联 FP# | FP8 |
| 前置条件 | 无 |
| 输入 | `collection_name='rss', key='不存在'` |
| 预期 | 抛出 ValueError("未找到ID为 不存在 的数据") |
| 验证点 | deleted_count=0 触发异常 |

### TC31: list_story_task_dirs — 基本查询

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC7 |
| 关联 FP# | FP11 |
| 前置条件 | sessions 集合有含 projectName='YiAi', storyName='api-routes' 的文档 |
| 输入 | 无过滤参数 |
| 预期 | 返回去重的项目-故事目录列表 |
| 验证点 | 同 projectName+storyName 只出现一次；dir_path 格式正确；session_count ≥ 1 |

### TC32: list_story_task_dirs — 按项目过滤

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC7 |
| 关联 FP# | FP11 |
| 前置条件 | sessions 有多个项目的文档 |
| 输入 | `project_name='YiAi'` |
| 预期 | 只返回 YiAi 项目的目录 |
| 验证点 | 结果中无其他项目名 |

### TC33: list_story_task_dirs — 空结果

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC7 |
| 关联 FP# | FP11 |
| 前置条件 | sessions 无 projectName 非空文档 |
| 输入 | 无过滤参数 |
| 预期 | `{list: [], total: 0, totalPages: 0}` |
| 验证点 | 优雅处理空结果 |

---

## Gate A 交接信号

| 检查项 | 状态 | 说明 |
|--------|:---:|------|
| 测试用例覆盖全部 AC# | ✓ | AC1–AC8 均有 ≥1 个 TC 覆盖 |
| 测试用例覆盖全部公共方法 | ✓ | 7 个方法 + mongo_store 差异点均有 TC |
| NoSQL 注入测试 | ✓ | TC6 验证 re.escape |
| 异常路径覆盖 | ✓ | 参数缺失、不存在、重复、无效格式 |
| 分页边界测试 | ✓ | TC14（上限）/ TC15（无效值） |
| 安全相关测试 | ✓ | TC6（注入）、TC18/TC26（去重）、TC12/TC13（信息泄露） |
| 双实现差异测试 | ✓ | TC25/TC26（mongo_store 特有路径） |

---

### 主要价值

- ✅ **AC 全覆盖** — 33 个测试用例覆盖全部 8 个验收条件
- 🛡️ **安全优先** — NoSQL 注入、信息泄露、数据去重均有专项测试
- 🔍 **边界完备** — 分页上限、字段投影、双实现差异、异常路径全部覆盖
- 📊 **双实现验证** — data_service 和 mongo_store 的差异点独立测试

---

## 回溯链

| 来源 | 路径 | 证据级别 |
|------|------|---------|
| 故事任务 | `YiAi-故事任务.md` §5 AC1–AC8 | A |
| 使用场景 | `YiAi-使用场景.md` 场景 1–6 | A |
| 技术评审 | `YiAi-技术评审.md` §2 API 签名 | A |
| 源码 | `src/services/database/data_service.py` | A |
| 源码 | `src/services/database/mongo_store.py` | A |

### 变更记录

| 日期 | 版本 | 变更内容 | 来源 |
|------|------|---------|------|
| 2026-05-22 | 1.0.0 | 初始文档基线，从源码反推生成 | /rui doc --from-code services-database |
