# YiAi-测试设计 — services-maintenance

> 系统维护子系统测试设计。2 组件 16 用例。
>
> **来源**：源码分析 | **证据等级**：B | **项目类型**：backend

---

## 测试用例

### TC1–TC3: session_service

| TC# | 场景 | 预期 |
|-----|------|------|
| TC1 | 获取全部 sessions | 返回 List[Dict]，含所有文档 |
| TC2 | 删除存在的 key | 返回 deleted_count=1 |
| TC3 | 删除不存在的 key | 返回 deleted_count=0 |

### TC4–TC8: 图片引用提取

| TC# | 场景 | 预期 |
|-----|------|------|
| TC4 | Markdown 图片引用 | `![alt](/static/img.png)` → {"img.png"} |
| TC5 | HTML img 标签 | `<img src="/static/photo.jpg">` → {"photo.jpg"} |
| TC6 | /static/ 路径引用 | `/static/uploads/icon.svg` → {"uploads/icon.svg"} |
| TC7 | URL 带查询参数 | `/static/img.png?v=2` → {"img.png"} |
| TC8 | 嵌套字段（list/dict） | `{"msgs": [{"text": "![](x.png)"}]}` → {"x.png"} |

### TC9–TC12: 图片清理

| TC# | 场景 | 预期 |
|-----|------|------|
| TC9 | dry_run=true | 返回统计，不实际删除文件 |
| TC10 | dry_run=false | 文件被 unlink，freed_space > 0 |
| TC11 | static 目录不存在 | 返回 total_images_found=0 |
| TC12 | 大小写不敏感回退 | Ref.jpg 匹配 ref.jpg |

### TC13–TC16: Session 清理

| TC# | 场景 | 预期 |
|-----|------|------|
| TC13 | session 引用不存在的图片 | 该 session 被标记/删除 |
| TC14 | session 无 key | 跳过 |
| TC15 | 正常 session（所有引用存在） | 不删除 |
| TC16 | cleanup_sessions=false | 不检查 sessions |

---

## Gate A 交接信号

| 检查项 | 状态 |
|--------|:---:|
| AC 全覆盖 (AC1–AC4) | ✓ |
| dry_run 安全机制 | ✓ (TC9) |
| 引用提取（3 正则 + 参数剥离） | ✓ (TC4–TC7) |
| 大小写回退 | ✓ (TC12) |

---

### 主要价值

- ✅ **16 用例覆盖 2 组件**
- 🔍 **引用提取完整** — 3 正则 + 参数剥离 + 嵌套递归
- 🛡️ **安全路径** — dry_run 预览 + 大小写回退
- 📊 **边界覆盖** — 不存在的目录/无 key session/空集合

---

## 回溯链

| 来源 | 路径 |
|------|------|
| 故事任务 | `YiAi-故事任务.md` §5 |
| 源码 | `src/api/routes/maintenance.py` |

### 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2026-05-22 | 1.0.0 | 初始 /rui doc --from-code |
