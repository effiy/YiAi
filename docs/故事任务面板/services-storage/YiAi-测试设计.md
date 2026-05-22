# YiAi-测试设计 — services-storage

> OSS 存储服务的测试设计文档。覆盖 `oss_client.py` 全部公共函数。
>
> **来源**：源码分析 `/rui doc --from-code services-storage`
> **证据等级**：B（只读源码 + 静态分析）
> **项目类型**：backend
>
> **注意**：`upload_file_to_oss` / `upload_bytes_to_oss` / `delete_oss_file` / `list_files` 依赖 OSS 连接，测试时需 mock `oss2.Bucket`。

---

## 测试用例

### TC1: upload_file_to_oss — 成功上传

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP1, FP3 |
| 前置条件 | mock OSS 配置完整，mock Bucket，文件 .jpg，大小 < 限制 |
| 输入 | `upload_file_to_oss(mock_uploadfile("test.jpg", b"data"))` |
| 预期 | 返回 {url, filename: "test.jpg", object_name} |
| 验证点 | put_object 被调用；url 格式为 `https://{bucket}.{endpoint}/{key}` |

### TC2: upload_file_to_oss — 扩展名不合法

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC2 |
| 关联 FP# | FP1, R1 |
| 前置条件 | mock OSS 配置完整 |
| 输入 | `upload_file_to_oss(mock_uploadfile("malware.exe", b"data"))` |
| 预期 | BusinessException(INVALID_PARAMS, "Unsupported file type: .exe") |
| 验证点 | 扩展名检查在大小检查之前 |

### TC3: upload_file_to_oss — 文件过大

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP1, R2 |
| 前置条件 | mock 文件大小 > oss_max_file_size |
| 输入 | `upload_file_to_oss(mock_uploadfile("big.jpg", oversized_bytes))` |
| 预期 | BusinessException(INVALID_PARAMS, "File too large") |
| 验证点 | put_object 不被调用 |

### TC4: upload_file_to_oss — 无文件名

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP1 |
| 前置条件 | mock 文件 filename 为空 |
| 输入 | `upload_file_to_oss(mock_uploadfile("", b"data"))` |
| 预期 | BusinessException(INVALID_PARAMS, "Filename required") |
| 验证点 | 参数校验 |

### TC5: upload_bytes_to_oss — 成功上传

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP2, FP3 |
| 前置条件 | mock OSS 配置完整，mock Bucket |
| 输入 | `upload_bytes_to_oss(b"data", "photo.jpg")` |
| 预期 | 返回 {url, filename: "photo.jpg", object_name} |
| 验证点 | bytes 直传路径正确 |

### TC6: upload_bytes_to_oss — filename 为空默认值

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP2 |
| 前置条件 | mock OSS 配置完整 |
| 输入 | `upload_bytes_to_oss(b"data", "")` |
| 预期 | filename 默认为 "image.png"，扩展名 .png |
| 验证点 | `safe_filename.strip() or "image.png"` 生效 |

### TC7: get_bucket — 配置不完整

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC3 |
| 关联 FP# | FP8, R3 |
| 前置条件 | OSSConfig 中 access_key_id 为空 |
| 输入 | `get_bucket(config)` |
| 预期 | RuntimeError("OSS configuration is incomplete") |
| 验证点 | 四项配置任一缺失即抛异常 |

### TC8: build_oss_url — URL 生成

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC1 |
| 关联 FP# | FP3, R8 |
| 前置条件 | bucket="my-bkt", endpoint="http://oss-cn.aliyuncs.com" |
| 输入 | `build_oss_url("my-bkt", "http://oss-cn.aliyuncs.com", "images/test.jpg")` |
| 预期 | `https://my-bkt.oss-cn.aliyuncs.com/images/test.jpg` |
| 验证点 | http:// 前缀被去除 |

### TC9: delete_oss_file — 成功删除

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC4 |
| 关联 FP# | FP4, R5 |
| 前置条件 | mock object_exists=True, mock Bucket + MongoDB |
| 输入 | `delete_oss_file("images/test.jpg")` |
| 预期 | 返回 "images/test.jpg"；delete_object 被调用；DB delete_one 被调用两次（tags + info） |
| 验证点 | 对象 + DB 关联全部清理 |

### TC10: delete_oss_file — 文件不存在

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC5 |
| 关联 FP# | FP4, R5 |
| 前置条件 | mock object_exists=False |
| 输入 | `delete_oss_file("images/ghost.jpg")` |
| 预期 | BusinessException(DATA_NOT_FOUND, "File not found") |
| 验证点 | delete_object 不被调用 |

### TC11: delete_oss_file — DB 清理失败降级

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC4 |
| 关联 FP# | FP4 |
| 前置条件 | mock DB delete_one 抛异常 |
| 输入 | `delete_oss_file("images/test.jpg")` |
| 预期 | 返回 "images/test.jpg"（不抛异常）；warning 日志记录 |
| 验证点 | DB 失败不阻断 OSS 删除 |

### TC12: set_file_tags — 正常设置

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC6 |
| 关联 FP# | FP6, R6 |
| 前置条件 | mock MongoDB |
| 输入 | `set_file_tags("test.jpg", ["A", "B", "A"])` |
| 预期 | 返回 {object_name: "test.jpg", tags: ["A", "B"]}；update_one upsert=True 被调用 |
| 验证点 | 标签去重（A 只出现一次）；空格去除 |

### TC13: set_file_tags — object_name 为空

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP6 |
| 前置条件 | 无 |
| 输入 | `set_file_tags("", ["A"])` |
| 预期 | ValueError("文件对象名不能为空") |
| 验证点 | 参数校验在 DB 操作之前 |

### TC14: get_file_tags — 有标签

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC6 |
| 关联 FP# | FP6 |
| 前置条件 | DB 中有 tags=["A", "B"] |
| 输入 | `get_file_tags("test.jpg")` |
| 预期 | 返回 ["A", "B"] |
| 验证点 | 标签列表正确返回 |

### TC15: get_file_tags — 无标签

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP6 |
| 前置条件 | DB 中无此对象的标签文档 |
| 输入 | `get_file_tags("unknown.jpg")` |
| 预期 | 返回 [] |
| 验证点 | 优雅处理不存在 |

### TC16: delete_file_tags — 删除成功

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP6 |
| 前置条件 | DB 中存在标签文档 |
| 输入 | `delete_file_tags("test.jpg")` |
| 预期 | 返回 True |
| 验证点 | deleted_count > 0 |

### TC17: get_all_tags — 聚合统计

| 字段 | 内容 |
|------|------|
| 关联 AC# | AC7 |
| 关联 FP# | FP6 |
| 前置条件 | DB 中有两个文件的标签 A:[tag1,tag2], B:[tag1] |
| 输入 | `get_all_tags()` |
| 预期 | [{name: "tag1", count: 2}, {name: "tag2", count: 1}] |
| 验证点 | 计数降序排列 |

### TC18: update_file_info — 设置标题

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP7, R7 |
| 前置条件 | mock MongoDB |
| 输入 | `update_file_info("test.jpg", title="新标题")` |
| 预期 | upsert 被调用；$set 含 title + updatedTime；$setOnInsert 含 createdTime |
| 验证点 | 时间戳字段自动维护 |

### TC19: get_file_info — 存在信息

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP7 |
| 前置条件 | DB 中有 title="标题", description="描述" |
| 输入 | `get_file_info("test.jpg")` |
| 预期 | {object_name, title: "标题", description: "描述"} |
| 验证点 | 信息完整返回 |

### TC20: get_file_info — 不存在信息

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP7 |
| 前置条件 | DB 中无此对象的信息文档 |
| 输入 | `get_file_info("unknown.jpg")` |
| 预期 | {object_name: "unknown.jpg", title: "", description: ""} |
| 验证点 | 优雅降级返回空值 |

### TC21: list_files — 基本列表

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP5 |
| 前置条件 | mock OSS ObjectIterator 返回 2 个文件 |
| 输入 | `list_files(directory="images/")` |
| 预期 | 返回 2 个文件的信息（含 name/size/url/tags/title/description） |
| 验证点 | 每个文件合并了 OSS 信息 + 标签 + 文件信息 |

### TC22: list_files — 标签过滤

| 字段 | 内容 |
|------|------|
| 关联 AC# | — |
| 关联 FP# | FP5 |
| 前置条件 | 文件 A 有标签 ["cat"]，文件 B 有标签 ["dog"] |
| 输入 | `list_files(tags="cat")` |
| 预期 | 仅返回文件 A |
| 验证点 | 标签过滤逻辑（any 匹配） |

---

## Gate A 交接信号

| 检查项 | 状态 | 说明 |
|--------|:---:|------|
| 测试用例覆盖全部 AC# | ✓ | AC1–AC7 全覆盖 |
| 测试用例覆盖全部公共函数 | ✓ | 12 个公共函数均有 TC |
| 安全校验测试 | ✓ | TC2（扩展名）/ TC3（大小）/ TC7（配置）/ TC10（不存在） |
| 异常降级测试 | ✓ | TC11（DB 清理失败）/ TC19/20（信息不存在） |
| 标签去重测试 | ✓ | TC12 |
| URL 构建测试 | ✓ | TC8 |

---

### 主要价值

- ✅ **AC 全覆盖** — 22 个测试用例
- 🛡️ **安全校验充分** — 扩展名/大小/配置完整性/存在性四层验证
- 🔗 **关联清理验证** — 删除文件时 OSS+DB 同步清理

---

## 回溯链

| 来源 | 路径 | 证据级别 |
|------|------|---------|
| 故事任务 | `YiAi-故事任务.md` §5 AC1–AC7 | A |
| 源码 | `src/services/storage/oss_client.py` | A |

### 变更记录

| 日期 | 版本 | 变更内容 | 来源 |
|------|------|---------|------|
| 2026-05-22 | 1.0.0 | 初始文档基线，从源码反推生成 | /rui doc --from-code services-storage |
