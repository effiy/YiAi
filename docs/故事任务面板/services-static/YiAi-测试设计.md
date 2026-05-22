# YiAi-测试设计 — services-static

> 静态文件管理子系统测试设计。2 组件 16 用例。
>
> **来源**：源码分析 | **证据等级**：B | **项目类型**：backend

---

## 测试用例

### TC1–TC8: upload_and_unzip

| TC# | 场景 | 预期 |
|-----|------|------|
| TC1 | 上传 .zip 文件 | 正常解压，返回文件数/目录数 |
| TC2 | 上传非 ZIP 文件 (.txt) | BusinessException("只支持ZIP格式文件") |
| TC3 | 文件超大小限制 | BusinessException 含大小限制提示 |
| TC4 | 指定 project_id 解压 | 文件解压到 static/<project_id>/ |
| TC5 | ZIP 含公共根目录 | 自动剥离前缀 |
| TC6 | ZIP 含 ../ 路径穿越 | 该条目被 _is_safe_path 拒绝跳过 |
| TC7 | ZIP 含非 UTF-8 文件名 | _decode_filename 回退链正确解码 |
| TC8 | 解压后临时文件清理 | temp_zip_path 被 unlink |

### TC9–TC12: _is_safe_path

| TC# | 场景 | 预期 |
|-----|------|------|
| TC9 | 正常路径 "foo/bar" | True |
| TC10 | 含 ../ 的路径 "../../etc/passwd" | False |
| TC11 | 以 / 开头的绝对路径 "/etc/passwd" | False |
| TC12 | 路径在 base_dir 外 | False |

### TC13–TC16: unzip_from_path

| TC# | 场景 | 预期 |
|-----|------|------|
| TC13 | 正常本地 ZIP 路径 | 解压成功，返回 success=True |
| TC14 | file_path 为空 | ValueError("file_path is required") |
| TC15 | 文件不存在 | ValueError("File not found") |
| TC16 | 无 project_id 时自动命名 | 目录名为 ZIP 文件名（无后缀） |

---

## Gate A 交接信号

| 检查项 | 状态 |
|--------|:---:|
| AC 全覆盖 (AC1–AC4) | ✓ |
| 格式校验 | ✓ (TC2) |
| 路径穿越防护 | ✓ (TC6, TC10, TC11, TC12) |
| 大小限制 | ✓ (TC3) |

---

### 主要价值

- ✅ **16 用例覆盖 2 组件**
- 🔒 **安全路径充分** — upload_and_unzip 4 校验全覆盖 + _is_safe_path 独立 4 用例
- 📦 **正常路径** — 基本解压 + 根目录剥离 + 编码兼容
- 🧹 **边界覆盖** — 空参数 + 不存在 + 格式错误 + 超大小

---

## 回溯链

| 来源 | 路径 |
|------|------|
| 故事任务 | `YiAi-故事任务.md` §5 |
| 源码 | `src/services/static/` |

### 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2026-05-22 | 1.0.0 | 初始 /rui doc --from-code |
