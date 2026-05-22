# YiAi-技术评审 — services-static

> 静态文件管理子系统技术评审。2 组件架构与接口设计。
>
> **来源**：源码分析 | **证据等级**：B | **项目类型**：backend → 跳过 §4/§5/§6

---

## 效果示意

```mermaid
flowchart TD
    subgraph ENTRY["入口层"]
        API["POST /api/upload/zip<br/>UploadFile + project_id"]:::api
        EXEC["execute_module<br/>archive_service.unzip_from_path"]:::api
    end

    subgraph CORE["核心处理"]
        VAL["格式+大小校验<br/>.zip + MAX_ZIP_SIZE"]:::val
        SAFE["路径安全校验<br/>_is_safe_path · normpath"]:::sec
        DECODE["编码兼容<br/>utf-8 → cp437 → ignore"]:::dec
        ROOT["公共根目录检测<br/>_find_common_root"]:::dec
        EXTRACT["逐条目解压<br/>跳过目录条目+不安全路径"]:::val
    end

    subgraph OUT["输出"]
        FILES["static/<project_id>/<br/>解压后的文件"]:::out
        RESULT["{extracted_files_count,<br/>extracted_dirs_count}"]:::out
    end

    API --> VAL --> SAFE --> ROOT --> EXTRACT --> FILES
    EXEC --> EXTRACT2["extractall 直接解压<br/>无路径校验"]:::warn
    EXTRACT2 --> FILES
    EXTRACT --> RESULT

    classDef api fill:#e3f2fd,stroke:#1565c0;
    classDef val fill:#fff3e0,stroke:#e65100;
    classDef sec fill:#e8f5e9,stroke:#2e7d32;
    classDef dec fill:#f3e5f5,stroke:#6a1b9a;
    classDef out fill:#e8f5e9,stroke:#2e7d32;
    classDef warn fill:#ffebee,stroke:#c62828;
```

---

## §1 架构设计

### 1.1 组件关系

| 组件 | 激活方式 | 安全校验 | 配置驱动 |
|------|---------|:---:|---------|
| upload_and_unzip | HTTP 文件上传 API | 格式+大小+路径+编码 | static_base_dir / static_max_zip_size |
| unzip_from_path | execute_module 调用 | 文件存在检查 | static_base_dir |

### 1.2 路径安全模型

```mermaid
flowchart LR
    INPUT["用户输入路径"]:::in --> NORM["os.path.normpath"]:::sec
    NORM --> CHECK1{"含 .. 或<br/>以 / 开头?"}:::sec
    CHECK1 -->|"是"| REJECT["拒绝"]:::bad
    CHECK1 -->|"否"| JOIN["join(base_dir, path)"]:::sec
    JOIN --> NORM2["再次 normpath"]:::sec
    NORM2 --> CHECK2{"以 base_dir<br/>开头?"}:::sec
    CHECK2 -->|"是"| ALLOW["放行"]:::ok
    CHECK2 -->|"否"| REJECT

    classDef in fill:#ffebee,stroke:#c62828;
    classDef sec fill:#e8f5e9,stroke:#2e7d32;
    classDef bad fill:#ffebee,stroke:#c62828;
    classDef ok fill:#e8f5e9,stroke:#2e7d32;
```

**注意**：unzip_from_path 未使用此安全模型，直接 `os.path.join(base_dir, project_id)` + `extractall`。

### 1.3 临时文件生命周期

```mermaid
flowchart LR
    READ["file.read()"]:::s --> WRITE["NamedTemporaryFile<br/>delete=False"]:::s
    WRITE --> EXTRACT["ZipFile 解压"]:::s
    EXTRACT --> CLEAN["finally: os.unlink"]:::s
    CLEAN -.异常.-> WARN["logger.warning"]:::warn

    classDef s fill:#e3f2fd,stroke:#1565c0;
    classDef warn fill:#fff3e0,stroke:#e65100;
```

---

## §2 API / 方法签名

### upload_and_unzip

```python
async def upload_and_unzip(
    file: UploadFile,
    project_id: Optional[str] = None
) -> Dict[str, Any]
```

| 参数 | 类型 | 说明 |
|------|------|------|
| file | UploadFile | ZIP 文件 |
| project_id | Optional[str] | 目标子目录名 |

返回值：`{filename, target_dir, extracted_files_count, extracted_dirs_count, project_id}`

### unzip_from_path

```python
async def unzip_from_path(params: Dict[str, Any]) -> Dict[str, Any]
```

| 参数 | 类型 | 说明 |
|------|------|------|
| file_path | str (必填) | 本地 ZIP 绝对路径 |
| project_id | str (可选) | 目标子目录名 |

---

## §3 数据设计

### 配置项

| 配置 | 说明 |
|------|------|
| static_base_dir | 静态文件根目录 |
| static_max_zip_size | ZIP 文件大小上限（字节） |

### 编码回退链

```
bytes → utf-8 decode
  ↓ 失败
cp437 bytes → utf-8 decode
  ↓ 失败
原始字符串（或 ignore 解码）
```

---

### 主要价值

- 📦 **ZIP 部署** — 上传自动解压，干净的文件级结果
- 🔒 **路径安全** — 4 步校验链：格式→大小→路径→编码
- 🧹 **资源管理** — 临时文件 finally 清理，单文件解压异常不阻断
- 🌐 **编码鲁棒** — 多平台 ZIP 文件名自动适配

---

## 回溯链

| 来源 | 路径 |
|------|------|
| 源码 | `src/services/static/static_files.py` |
| 源码 | `src/services/static/archive_service.py` |
| 故事任务 | `YiAi-故事任务.md` |

### 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2026-05-22 | 1.0.0 | 初始 /rui doc --from-code |
