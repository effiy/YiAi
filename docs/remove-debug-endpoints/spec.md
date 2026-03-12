# 去除 Debug/Health Endpoints 详细设计方案

## 概述

本文档详细描述如何从 YiAi 项目中移除 Debug/Health 相关 endpoints 的技术实现方案。

## 需求追溯

本文档基于需求文档：[plan.md](plan.md)

## 当前实现分析

### 1. Debug 路由模块 (`src/api/routes/debug.py`)

当前实现非常简单，仅包含一个端点：

```python
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/debug", include_in_schema=False)
async def debug_page():
    """
    API 调试页面
    """
    return FileResponse("static/index.html")
```

**功能说明**：
- 路径：`GET /debug`
- 功能：返回 `static/index.html` 作为调试页面
- `include_in_schema=False`：不在 OpenAPI 文档中显示

### 2. 路由注册链路

**第一步：`src/api/routes/__init__.py`**
```python
"""API routes package."""
from . import debug
from . import execution
from . import upload
from . import wework
from . import maintenance

__all__ = ["debug", "execution", "upload", "wework", "maintenance"]
```

**第二步：`src/main.py`**
```python
from api.routes import debug, execution, upload, wework, maintenance

# 在 create_app() 函数中：
app.include_router(debug.router, tags=["Debug"])
app.include_router(execution.router, tags=["Execution"])
app.include_router(upload.router, tags=["Upload"])
app.include_router(wework.router, tags=["WeWork"])
app.include_router(maintenance.router, tags=["Maintenance"])
```

## 实现方案

### 步骤 1：删除 debug.py 文件

**操作**：
- 删除文件：`/src/api/routes/debug.py`

**验证**：
- 确认文件已从文件系统中移除

### 步骤 2：更新 routes/__init__.py

**修改前**：
```python
"""API routes package."""
from . import debug
from . import execution
from . import upload
from . import wework
from . import maintenance

__all__ = ["debug", "execution", "upload", "wework", "maintenance"]
```

**修改后**：
```python
"""API routes package."""
from . import execution
from . import upload
from . import wework
from . import maintenance

__all__ = ["execution", "upload", "wework", "maintenance"]
```

**变更内容**：
- 移除 `from . import debug` 导入语句
- 从 `__all__` 列表中移除 `"debug"`

### 步骤 3：更新 src/main.py

**修改位置 1：导入语句**

**修改前**：
```python
from api.routes import debug, execution, upload, wework, maintenance
```

**修改后**：
```python
from api.routes import execution, upload, wework, maintenance
```

**修改位置 2：路由注册**

**修改前**：
```python
# 注册 API 路由
app.include_router(debug.router, tags=["Debug"])
app.include_router(execution.router, tags=["Execution"])
app.include_router(upload.router, tags=["Upload"])
app.include_router(wework.router, tags=["WeWork"])
app.include_router(maintenance.router, tags=["Maintenance"])
```

**修改后**：
```python
# 注册 API 路由
app.include_router(execution.router, tags=["Execution"])
app.include_router(upload.router, tags=["Upload"])
app.include_router(wework.router, tags=["WeWork"])
app.include_router(maintenance.router, tags=["Maintenance"])
```

**变更内容**：
- 移除 `debug` 的导入
- 移除 `app.include_router(debug.router, tags=["Debug"])` 语句

### 步骤 4：验证整个代码库

**检查项**：
1. 使用 grep 搜索整个代码库中是否还有 "debug" 的引用
2. 确认没有其他模块导入或引用 debug 路由

**搜索命令**：
```bash
# 搜索 Python 文件中的 debug 引用
grep -r "debug" --include="*.py" src/

# 搜索是否有其他引用
grep -r "debug.router" src/
grep -r "from .*debug" src/
```

## 文件变更清单

| 文件路径 | 操作类型 | 说明 |
|---------|---------|------|
| `src/api/routes/debug.py` | 删除 | 完全移除该文件 |
| `src/api/routes/__init__.py` | 修改 | 移除 debug 模块的导入和导出 |
| `src/main.py` | 修改 | 移除 debug 路由的导入和注册 |

## 回滚方案

如果需要回滚此变更，可以通过以下步骤恢复：

```bash
# 1. 恢复删除的文件
git checkout <commit-hash> -- src/api/routes/debug.py

# 2. 恢复 __init__.py
git checkout <commit-hash> -- src/api/routes/__init__.py

# 3. 恢复 main.py
git checkout <commit-hash> -- src/main.py
```

其中 `<commit-hash>` 是实施变更之前的 commit 哈希值。

## 测试验证计划

### 1. 静态检查

- [ ] 确认 `src/api/routes/debug.py` 不存在
- [ ] 确认 `__init__.py` 中无 debug 引用
- [ ] 确认 `main.py` 中无 debug 引用
- [ ] 运行 Python 语法检查：`python -m py_compile src/main.py src/api/routes/__init__.py`

### 2. 应用启动测试

- [ ] 执行 `python main.py` 启动应用
- [ ] 检查启动日志无错误
- [ ] 确认服务在 http://localhost:8000 正常运行
- [ ] 访问 http://localhost:8000/docs 确认 API 文档正常显示

### 3. 端点验证测试

- [ ] 访问 `GET /debug` 应返回 404 Not Found
- [ ] 访问 `GET /docs` 确认没有 Debug 标签的端点
- [ ] 测试其他 endpoints 功能正常：
  - [ ] `GET /execution` - 应正常工作（或返回相应的参数错误）
  - [ ] `POST /upload` - 应正常工作
  - [ ] 其他 maintenance、wework 端点应正常

### 4. 集成测试（如适用）

- [ ] 运行现有的测试套件（如果有）
- [ ] 确保所有测试通过

## 风险与缓解措施

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| 意外删除了其他文件 | 低 | 高 | 使用 git 管理，随时可以回滚 |
| 代码中存在未发现的 debug 引用 | 低 | 中 | 仔细进行 grep 搜索检查 |
| 应用启动失败 | 低 | 高 | 修改前先备份，修改后立即测试启动 |
| 其他 endpoints 受影响 | 低 | 高 | 修改后全面测试所有 endpoints |

## 实施检查清单

- [ ] 创建 git feature 分支
- [ ] 删除 `src/api/routes/debug.py`
- [ ] 修改 `src/api/routes/__init__.py`
- [ ] 修改 `src/main.py`
- [ ] 执行 grep 搜索确认无遗漏引用
- [ ] 执行 Python 语法检查
- [ ] 启动应用验证正常
- [ ] 测试 `/debug` 返回 404
- [ ] 测试其他 endpoints 功能正常
- [ ] 提交变更
- [ ] Code Review
- [ ] 合并到主分支

## 附录

### A. 完整的 diff 预览

**src/api/routes/__init__.py**:
```diff
--- a/src/api/routes/__init__.py
+++ b/src/api/routes/__init__.py
@@ -1,8 +1,7 @@
 """API routes package."""
-from . import debug
 from . import execution
 from . import upload
 from . import wework
 from . import maintenance

-__all__ = ["debug", "execution", "upload", "wework", "maintenance"]
+__all__ = ["execution", "upload", "wework", "maintenance"]
```

**src/main.py**:
```diff
--- a/src/main.py
+++ b/src/main.py
@@ -21,7 +21,7 @@ from core.middleware import header_verification_middleware
 from core.logger import setup_logging
 from core.exception_handler import register_exception_handlers
-from api.routes import debug, execution, upload, wework, maintenance
+from api.routes import execution, upload, wework, maintenance

 # 导入服务模块
 from services.rss.rss_scheduler import init_rss_system, shutdown_rss_system
@@ -88,7 +88,6 @@ def create_app(

     # 注册 API 路由
-    app.include_router(debug.router, tags=["Debug"])
     app.include_router(execution.router, tags=["Execution"])
     app.include_router(upload.router, tags=["Upload"])
     app.include_router(wework.router, tags=["WeWork"])
```
