# 项目初始化需求任务

> 用户故事、场景与前置条件。

---

## 用户故事

### US-1：作为开发者，我需要快速启动本地开发环境

**场景**：新成员加入项目，需要在一台新机器上运行服务。

**前置条件**：
- Python >= 3.10 已安装
- MongoDB 服务已运行
- 已克隆代码仓库

**验收标准**：
- [ ] 执行 `pip install -r requirements.txt` 成功
- [ ] 执行 `python main.py` 后服务在 `http://0.0.0.0:8000` 启动
- [ ] 访问 `/docs` 能看到 Swagger API 文档

### US-2：作为运维人员，我需要清晰的配置方式

**场景**：在不同环境（开发/测试/生产）部署服务。

**前置条件**：
- 有对应环境的 MongoDB 实例
- 已了解配置项含义

**验收标准**：
- [ ] 通过 `config.yaml` 能完成基础配置
- [ ] 环境变量能覆盖 YAML 配置
- [ ] 敏感配置（如 OSS key、auth token）不硬编码在代码中

### US-3：作为开发者，我需要理解项目架构和代码规范

**场景**：需要修改或新增功能。

**前置条件**：
- 已阅读项目文档

**验收标准**：
- [ ] 目录结构清晰，知道新增文件放在哪里
- [ ] 代码风格统一（命名、类型注解、文档字符串）
- [ ] 有明确的开发工作流指引

### US-4：作为使用者，我需要 API 具备基本的认证保护

**场景**：生产环境部署，防止未授权访问。

**前置条件**：
- 已配置 `API_X_TOKEN` 或 `middleware.auth_token`

**验收标准**：
- [ ] 未携带 `X-Token` 的请求被拦截（401）
- [ ] 携带正确 `X-Token` 的请求正常通过
- [ ] 白名单路径（文件操作、静态资源）无需认证

### US-5：作为开发者，我需要动态执行模块的能力

**场景**：通过 API 调用业务逻辑，无需新增路由。

**前置条件**：
- 目标模块和方法已在 `module.allowlist` 中

**验收标准**：
- [ ] 通过 GET/POST `/execution` 能调用白名单中的模块方法
- [ ] 支持同步/异步函数、生成器、SSE 流式传输
- [ ] 不在白名单中的模块返回 403

### US-6：作为开发者，我需要结构化状态存储能力

**场景**：需要在服务端持久化记录技能执行结果、运行时状态等结构化数据。

**前置条件**：
- State Store 服务已启用（`state_store.enabled: true`）
- MongoDB 连接正常

**验收标准**：
- [ ] 通过 POST `/state/records` 能创建状态记录
- [ ] 通过 GET `/state/records` 能按 record_type、tags、title 等条件查询
- [ ] 查询结果支持分页（pageNum、pageSize、totalPages）
- [ ] 通过 PUT `/state/records/{key}` 能更新记录
- [ ] 通过 DELETE `/state/records/{key}` 能删除记录
- [ ] 通过 CLI `python src/cli/state_query.py list` 能查询记录

### US-7：作为运维人员，我需要可靠性监控能力

**场景**：生产环境需要请求限流、慢请求检测和执行安全防护。

**前置条件**：
- Observer 系统已启用（`observer.enabled: true`）

**验收标准**：
- [ ] 超过 `throttle_max_requests` 的请求返回 429，code=1003
- [ ] `throttle_whitelist` 中的 IP 不受限流影响
- [ ] 慢请求（>slow_threshold_ms）和错误请求（>=500）被采样记录
- [ ] `GET /health/observer` 返回 Observer 各组件状态
- [ ] ReentrancyGuard 在超限时抛出 ReentrancyExceeded

### US-8：作为开发者，我需要 CLI 工具查询状态数据

**场景**：需要在不写代码的情况下快速查询和导出状态记录。

**前置条件**：
- State Store 服务已启用
- Python 环境已安装 typer 和 rich

**验收标准**：
- [ ] `python src/cli/state_query.py list` 支持表格、JSON、CSV 三种输出格式
- [ ] `python src/cli/state_query.py get <key>` 返回单条记录
- [ ] `python src/cli/state_query.py export -o out.json` 导出记录到文件
- [ ] `python src/cli/state_query.py stats` 显示记录总数统计
- [ ] 记录不存在时返回清晰的错误提示并 exit(1)

## 依赖关系

```
US-1 (环境启动)
  └─> US-2 (配置管理)
  └─> US-3 (架构理解)
US-4 (认证保护)
  └─> US-2 (配置管理)
US-5 (模块执行)
  └─> US-3 (架构理解)
US-6 (状态存储)
  └─> US-1 (环境启动)
  └─> US-4 (认证保护)
US-7 (可靠性监控)
  └─> US-2 (配置管理)
US-8 (CLI 工具)
  └─> US-6 (状态存储)
```

## Postscript: Future Planning & Improvements

- 增加容器化部署相关用户故事（Docker、docker-compose）
- 增加 CI/CD 流水线配置需求
- 增加数据库迁移和备份策略需求

## Workflow Standardization Review

1. **Repetitive labor identification**: 用户故事的验收标准与动态检查清单存在大量重复项。
2. **Decision criteria missing**: 用户故事拆分的粒度（何时合并/拆分）缺乏标准。
3. **Information silos**: 依赖关系图在 02 中手绘，与 05 检查清单的依赖无自动关联。
4. **Feedback loop**: 验收标准的验证结果缺乏向 02 文档的自动反馈。

## System Architecture Evolution Thinking

- **A1. Current architecture bottleneck**: 依赖关系图为手绘文本，无法交互式追踪。
- **A2. Next natural evolution node**: 使用可机器读取的依赖格式，自动生成依赖关系图。
- **A3. Risks and rollback plans for evolution**: 格式迁移可能丢失当前手绘图中的隐含依赖关系。
