# YiAi-故事任务 — services-storage

> OSS 存储服务层故事任务文档。覆盖 `oss_client.py`（上传/删除/标签/文件信息/列表）。
>
> **来源**：源码分析 `/rui doc --from-code services-storage`
> **证据等级**：B（只读源码 + 静态分析）
> **项目类型**：backend

---

## 效果示意

```mermaid
flowchart LR
    NOW["当前状态<br/>OSS 存储服务无文档基线"]:::pain
    NOW --> M1["里程碑 1<br/>故事任务基线建立"]:::milestone
    M1 --> GOAL["目标状态<br/>存储服务文档完整"]:::goal

    classDef pain fill:#ffebee,stroke:#c62828;
    classDef milestone fill:#fff3e0,stroke:#e65100;
    classDef goal fill:#e8f5e9,stroke:#2e7d32;
```

---

## §1 Story

### Story 1: 文件上传

| 字段 | 内容 |
|------|------|
| 作为 | 前端用户或 API 调用方 |
| 我想要 | 通过 HTTP 上传文件或直接上传字节内容到云端存储 |
| 以便 | 文件持久化存储并可公开访问 |
| 优先级 | P0 |
| 范围边界 | 上传到配置的 OSS Bucket，类型和大小受配置限制 |
| 依赖 | OSS 配置完整（access_key/secret_key/endpoint/bucket） |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 上传表单文件 | 调用 `upload_file_to_oss` 传入 UploadFile | 校验扩展名 → 校验大小 → 生成时间戳文件名 → put_object | 返回 {url, filename, object_name} |
| 2 | 上传字节内容 | 调用 `upload_bytes_to_oss` 传入 bytes + filename | 校验扩展名 → 校验大小 → 生成对象名 → put_object | 返回 {url, filename, object_name} |
| 3 | 上传到指定目录 | 传入 directory 参数 | 对象名格式 `{directory}/{timestamp}{ext}` | 文件存入指定目录前缀 |

---

### Story 2: 文件管理

| 字段 | 内容 |
|------|------|
| 作为 | 文件管理员 |
| 我想要 | 删除文件、查看文件列表、按标签筛选 |
| 以便 | 管理云端存储的文件资产 |
| 优先级 | P0 |
| 范围边界 | 仅操作已配置的 OSS Bucket |
| 依赖 | Story 1 上传能力 + OSS 连接 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 删除文件 | 调用 `delete_oss_file` 传入 object_name | 检查存在 → delete_object → 清理 DB 标签和信息 | 返回 object_name |
| 2 | 列出目录文件 | 调用 `list_files` 传入 directory | 遍历 ObjectIterator → 获取标签和信息 → 合并返回 | 返回文件列表（含 url/size/tags/title） |
| 3 | 按标签过滤 | 调用 `list_files` 传入 tags 参数 | 列出后过滤含指定标签的文件 | 仅返回匹配文件 |

---

### Story 3: 文件标签与信息

| 字段 | 内容 |
|------|------|
| 作为 | 内容管理者 |
| 我想要 | 为文件打标签、添加标题和描述 |
| 以便 | 更好地组织和检索文件 |
| 优先级 | P1 |
| 范围边界 | 标签和信息存储在 MongoDB，不写入 OSS 对象元数据 |
| 依赖 | Story 1 + 2 文件能力 |

#### §1.1 User Operations

| # | 操作 | 触发条件 | 操作步骤 | 预期结果 |
|---|------|---------|---------|---------|
| 1 | 设置标签 | 调用 `set_file_tags` 传入 tags 列表 | 去重 → upsert 到 collection_oss_file_tags | 返回 {object_name, tags} |
| 2 | 获取标签 | 调用 `get_file_tags` | find_one → 返回 tags 数组 | 返回标签列表（无则空） |
| 3 | 删除标签 | 调用 `delete_file_tags` | delete_one → 返回是否删除 | 标签被移除 |
| 4 | 查看所有标签 | 调用 `get_all_tags` | 聚合所有文档 → 按使用次数排序 | 返回 [{name, count}, ...] |
| 5 | 更新文件信息 | 调用 `update_file_info` 传入 title/description | upsert → 自动维护 createdTime/updatedTime | 返回 {object_name, title, description} |
| 6 | 获取文件信息 | 调用 `get_file_info` | find_one → 返回 title/description | 返回信息（无则空值） |

---

## §2 Requirements

### 功能点

| FP# | 描述 | 输入 | 输出 | 错误行为 | 优先级 |
|-----|------|------|------|---------|--------|
| FP1 | 文件上传 — 扩展名白名单 + 文件大小限制 + 时间戳命名 | UploadFile + directory(可选) | {url, filename, object_name} | 扩展名不允许/文件过大 → 400；OSS 配置不完整 → RuntimeError | P0 |
| FP2 | 字节上传 — 同 FP1 但接受 bytes | bytes + filename + directory(可选) | {url, filename, object_name} | 同 FP1；filename 为空时默认 image.png | P0 |
| FP3 | URL 构建 — 生成 `https://{bucket}.{endpoint}/{key}` 格式 | bucket_name + endpoint + object_key | HTTPS URL | — | P0 |
| FP4 | 文件删除 — 含关联标签和信息清理 | object_name | object_name | 文件不存在 → 404；DB 清理失败仅 warning | P0 |
| FP5 | 目录文件列表 — OSS ObjectIterator + 标签信息合并 | directory(可选) + tags(可选) | 文件列表 [{name, size, url, tags, title, description}] | — | P1 |
| FP6 | 标签 CRUD — 设置/获取/删除/聚合 | object_name + tags | 标签数据 | object_name 为空 → ValueError | P1 |
| FP7 | 文件信息 — 更新/获取标题和描述（自动时间戳） | object_name + title/description | {object_name, title, description} | object_name 为空 → ValueError | P1 |
| FP8 | OSS 配置校验 — 四项配置任一项缺失即运行时错误 | — | Bucket 实例或 RuntimeError | RuntimeError("OSS configuration is incomplete") | P0 |

### 业务规则

| R# | 描述 | 校验方式 | 证据级别 |
|----|------|---------|---------|
| R1 | 文件扩展名必须在 ALLOWED_EXTENSIONS 白名单内 | `oss_client.py`:74–76 — `if file_ext not in ALLOWED_EXTENSIONS` | A |
| R2 | 文件大小不能超过 `oss_max_file_size` 配置值 | `oss_client.py`:79–80 — `if len(content) > settings.oss_max_file_size` | A |
| R3 | OSS 四项配置（key/secret/endpoint/bucket）缺失时抛 RuntimeError | `get_bucket()`:42–43 | A |
| R4 | 对象名格式 `{directory/}{timestamp}{ext}`，directory 为空时不加 `/` | `oss_client.py`:83 | A |
| R5 | 删除文件时先检查对象存在性，不存在的文件返回 404 | `delete_oss_file()`:142–143 — `bucket.object_exists()` | A |
| R6 | 标签存储使用 upsert 模式（设置/覆盖而非追加） | `set_file_tags()`:182–192 — update_one upsert=True | A |
| R7 | 文件信息 upsert 时 $setOnInsert 设置 createdTime，每次 $set 刷新 updatedTime | `update_file_info()`:280–287 | A |
| R8 | URL 构建时自动去除 endpoint 中已有的 http/https 前缀 | `build_oss_url()`:59 — `replace('http://', '').replace('https://', '')` | A |

### 数据约束

| 约束 | 类型 | 范围/格式 | 来源 |
|------|------|----------|------|
| ALLOWED_EXTENSIONS | set | 配置 `oss_allowed_extensions` 中定义（默认 .jpg/.jpeg/.png） | config.yaml |
| oss_max_file_size | int | 配置值（默认 50MB = 52,428,800 字节） | config.yaml |
| object_name | string | `{directory/}{YYYYmmdd_HHMMSS}{ext}` | oss_client.py:82–83 |
| tags | List[str] | 去重后的非空字符串列表 | `set_file_tags()`:176–177 |
| oss_url | string | `https://{bucket}.{endpoint}/{object_key}` | `build_oss_url()` |

---

## §3 成功标准

| SC# | 描述 | 度量方式 | 目标值 | 优先级 | 关联 FP# |
|-----|------|---------|--------|--------|---------|
| SC1 | 用户可上传合法文件并获得可访问 URL | 上传 .jpg 文件 → 检查返回 url | url 为有效 HTTPS 地址 | P0 | FP1, FP3 |
| SC2 | 非法扩展名被拒绝 | 上传 .exe 文件 | BusinessException(INVALID_PARAMS) | P0 | FP1 |
| SC3 | 超大文件被拒绝 | 上传 > max_file_size 的文件 | BusinessException(INVALID_PARAMS) | P0 | FP1 |
| SC4 | OSS 配置不完整时快速失败 | 清空 OSS 配置 → 调用上传 | RuntimeError | P0 | FP8 |
| SC5 | 文件删除同时清理关联标签和信息 | 有标签的文件 → 删除 → 查询标签 | 标签和信息均被清理 | P1 | FP4, FP6 |

---

## §4 范围边界

### 范围内

| # | 条目 | 关联 FP# | 边界说明 |
|---|------|---------|---------|
| 1 | OSS 文件上传（UploadFile + bytes） | FP1, FP2 | 扩展名/大小校验 + 时间戳命名 |
| 2 | OSS 文件删除含关联数据清理 | FP4 | 删除对象 + 清理 DB 标签和信息 |
| 3 | 文件标签 CRUD + 聚合统计 | FP6 | MongoDB 存储，upsert 模式 |
| 4 | 文件信息管理（标题/描述） | FP7 | MongoDB 存储，自动时间戳 |
| 5 | 目录文件列表 + 标签过滤 | FP5 | OSS ObjectIterator + DB 合并 |

### 范围外

| # | 条目 | 排除原因 | 替代方案 |
|---|------|---------|---------|
| 1 | Bucket 创建和管理 | 由运维通过 OSS 控制台管理 | — |
| 2 | 文件访问权限控制 | OSS Bucket 策略配置（运维层面） | OSS RAM 策略 |
| 3 | 分片上传/断点续传 | 当前仅支持小文件直传 | oss2 SDK 支持但未集成 |

---

## §5 AC

| AC# | Given | When | Then | 门禁 |
|-----|-------|------|------|------|
| AC1 | OSS 配置完整，文件类型合法、大小合法 | 调用 upload_file_to_oss(file) | 返回 {url, filename, object_name}，文件在 OSS 中可访问 | Gate A |
| AC2 | 文件扩展名为 .exe | 调用 upload_file_to_oss(file) | BusinessException("Unsupported file type: .exe") | Gate A |
| AC3 | OSS 配置不完整 | 调用任意需要 Bucket 的方法 | RuntimeError("OSS configuration is incomplete") | Gate A |
| AC4 | object_name 指向已存在的对象 | 调用 delete_oss_file(object_name) | 对象被删除，MongoDB 中标签和信息被清理 | Gate A |
| AC5 | object_name 指向不存在的对象 | 调用 delete_oss_file(object_name) | BusinessException(DATA_NOT_FOUND, "File not found") | Gate A |
| AC6 | 给文件设置标签 ["A", "B"] | 调用 set_file_tags + get_file_tags | 返回 ["A", "B"]（无重复） | Gate A |
| AC7 | 调用 get_all_tags | 所有文件的标签聚合 | 返回 [{name, count}, ...] 按 count 降序 | Gate A |

---

## §6 风险与假设

| # | 风险/假设 | 类型 | 可能性 | 影响 | 缓解/验证策略 | 关联 FP# |
|---|----------|------|--------|------|-------------|---------|
| 1 | OSS 服务不可用导致上传/删除失败 | 风险 | M | H | OSS SDK 内置重试；快速失败 + 明确错误 | FP1, FP2, FP4 |
| 2 | 上传文件大小在配置值和 OSS 限额之间 | 风险 | L | L | 配置文件层面控制 | FP1, FP2 |
| 3 | DB 标签/信息清理失败导致孤儿数据 | 风险 | L | L | delete_oss_file 中清理失败仅 warning，不阻断删除 | FP4 |
| 4 | OSS 配置正确且 Bucket 已创建 | 假设 | — | — | get_bucket() 校验四项配置非空 | FP8 |

---

### 主要价值

- 📤 **双模式上传** — 支持 FastAPI UploadFile 和原始 bytes 两种上传方式
- 🛡️ **安全校验** — 扩展名白名单 + 文件大小限制 + OSS 配置完整性检查
- 🏷️ **标签系统** — 文件标签 CRUD + 全局聚合统计，支持按标签筛选
- 📋 **元数据管理** — 文件标题/描述独立管理，自动维护创建/更新时间
- 🔗 **关联清理** — 删除文件时自动清理 DB 中的标签和信息

---

## 回溯链

| 来源 | 路径 | 证据级别 |
|------|------|---------|
| 源码 | `src/services/storage/oss_client.py` (366 lines) | A |
| 配置 | `config.yaml` — oss.* | B |

### 变更记录

| 日期 | 版本 | 变更内容 | 来源 |
|------|------|---------|------|
| 2026-05-22 | 1.0.0 | 初始文档基线，从源码反推生成 | /rui doc --from-code services-storage |
