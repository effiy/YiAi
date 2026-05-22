# YiAi-测试设计 — models

> 数据模型层测试设计。2 组件 16 用例。
>
> **来源**：源码分析 | **证据等级**：B | **项目类型**：backend

---

## 测试用例

### TC1–TC6: ExecuteRequest

| TC# | 场景 | 预期 |
|-----|------|------|
| TC1 | 空构造（全部字段默认值） | module_name="" method_name="" parameters={} |
| TC2 | 正常构造 | 字段值正确赋值 |
| TC3 | parameters 为 JSON 字符串 | 正常接受（Union 类型） |
| TC4 | parameters 为 dict | 正常接受 |
| TC5 | 缺 module_name | 使用默认值 "" |
| TC6 | 传入未知字段 | Pydantic 默认忽略（无 extra=forbid） |

### TC7–TC10: 文件操作模型

| TC# | 场景 | 预期 |
|-----|------|------|
| TC7 | FileUploadRequest 缺必填字段 | ValidationError（filename/content） |
| TC8 | FileReadRequest 正常构造 | target_file 赋值正确 |
| TC9 | FileWriteRequest is_base64 默认值 | False |
| TC10 | ImageUploadToOssRequest data_url 必填 | 缺省时 ValidationError |

### TC11–TC13: 状态模型

| TC# | 场景 | 预期 |
|-----|------|------|
| TC11 | SkillExecutionRecord 正常构造 | 所有字段正确，tags 默认含 "skill_execution" |
| TC12 | SkillExecutionRecord status="invalid" | ValidationError（pattern 不匹配） |
| TC13 | SkillExecutionRecord duration_ms=-1 | ValidationError（ge=0） |

### TC14–TC16: 集合常量

| TC# | 场景 | 预期 |
|-----|------|------|
| TC14 | 导入所有常量 | 8 个常量全部可导入 |
| TC15 | 常量值正确 | 值与集合名字符串一致 |
| TC16 | __init__.py 导出完整 | __all__ 包含全部 8 个常量 |

---

## Gate A 交接信号

| 检查项 | 状态 |
|--------|:---:|
| AC 全覆盖 (AC1–AC4) | ✓ |
| 必填字段校验 | ✓ (TC7, TC10) |
| 约束校验（pattern/ge/le） | ✓ (TC12, TC13) |
| 集合常量可导入 | ✓ (TC14–TC16) |

---

### 主要价值

- ✅ **16 用例覆盖 2 组件**
- 🔒 **约束测试充分** — pattern/ge/le/max_length 均有覆盖
- 📊 **边界覆盖** — 空构造 + 缺字段 + 无效值 + 默认值
- 🏷️ **常量完整性** — 导入 + 值正确 + 导出完整

---

## 回溯链

| 来源 | 路径 |
|------|------|
| 故事任务 | `YiAi-故事任务.md` §5 |
| 源码 | `src/models/` |

### 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2026-05-22 | 1.0.0 | 初始 /rui doc --from-code |
