# 去除 Debug/Health Endpoints 功能需求

## 背景

当前 YiAi 项目中包含 Debug 相关的 endpoints，这些端点主要用于开发调试目的，在生产环境中可能带来安全风险。

## 目标

移除项目中的 Debug/Health 相关 endpoints，提高生产环境的安全性。

## 受影响的文件

### 1. API 路由文件

- `/src/api/routes/debug.py` - Debug 端点定义文件
- `/src/api/routes/__init__.py` - 路由包导出文件
- `/src/main.py` - FastAPI 应用注册路由处

### 2. 当前 Debug 端点

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/debug` | API 调试页面 |

## 需求说明

### 必须做的（Required）

1. **移除 debug.py 文件**
   - 删除 `/src/api/routes/debug.py` 文件

2. **更新路由注册**
   - 从 `/src/api/routes/__init__.py` 中移除 debug 模块的导入和导出
   - 从 `/src/main.py` 中移除 `app.include_router(debug.router)` 注册代码

3. **清理引用**
   - 确保整个代码库中没有其他对 debug 路由的引用

### 可选的（Optional）

- 如果未来需要健康检查功能，可以考虑实现独立的、带认证的 health check 端点
- 考虑在日志中添加启动成功的标记，替代 debug 端点的部分功能

## 验证标准

- [ ] `/src/api/routes/debug.py` 文件已删除
- [ ] `/src/api/routes/__init__.py` 中无 debug 相关引用
- [ ] `/src/main.py` 中无 debug 路由注册
- [ ] 应用启动正常，无错误日志
- [ ] 访问 `/debug` 返回 404 Not Found
- [ ] 其他 endpoints（execution、upload、wework、maintenance）功能正常

## 风险评估

- **低风险**：Debug endpoints 仅用于开发调试，不影响核心业务功能
- **回滚方案**：如需要恢复，通过 git 恢复相关文件即可

## 相关文件

- `/src/api/routes/debug.py`
- `/src/api/routes/__init__.py`
- `/src/main.py`
