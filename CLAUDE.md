# CLAUDE.md

## 项目画像

- **项目名**：YiAi（宜 AI）
- **类型**：后端服务（Python / FastAPI）
- **版本**：1.0.0
- **仓库**：git@github.com:effiy/YiAi.git
- **入口**：`main.py`（生产入口）、`src/main.py`（应用工厂）
- **架构**：src-layout 单体后端
- **数据库**：MongoDB（motor 异步驱动）
- **配置**：`config.yaml` + pydantic-settings（自定义 YAML 扁平化源）
- **安全面**：用户输入（API 路由参数/JSON body）· API（X-Token 认证）· 存储（MongoDB / OSS / 本地文件）· 认证（header_verification_middleware）· 第三方（Ollama / RSS 源 / 企业微信 Webhook）

### 模块地图

```
src/
├── api/routes/         # HTTP 路由层（FastAPI Router）
│   ├── execution.py    # 通用模块执行（GET/POST + SSE 流）
│   ├── upload.py       # 文件/图片上传/读取/写入/删除/重命名
│   ├── wework.py       # 企业微信机器人 Webhook
│   ├── maintenance.py  # 维护接口（缓存清理等）
│   ├── state.py        # 状态记录 CRUD 接口
│   └── observer_health.py # Observer 健康检查
├── core/               # 核心基础设施
│   ├── config.py       # Settings（YAML → pydantic 扁平化）
│   ├── database.py     # MongoDB 单例 + CRUD 包装
│   ├── middleware.py   # X-Token 认证中间件
│   ├── response.py     # 标准响应对象 / success() / fail()
│   ├── error_codes.py  # 错误码枚举（1xxx 客户端 / 5xxx 服务端）
│   ├── exceptions.py   # BusinessException
│   ├── logger.py       # 日志配置
│   ├── utils.py        # 文本/时间/数字/集合工具函数
│   └── observer/       # Observer 可靠性子系统
│       ├── throttle.py  # 限流中间件
│       ├── sampler.py   # 尾部采样（慢请求捕获）
│       ├── sandbox.py   # 文件系统/网络沙箱
│       ├── lazy_start.py# 懒启动管理器
│       └── guard.py     # 重入守卫
├── models/
│   ├── schemas.py      # Pydantic 请求/响应模型
│   └── collections.py  # MongoDB 集合名常量
├── services/
│   ├── execution/executor.py  # 受控模块执行器（白名单+沙箱+守卫）
│   ├── database/data_service.py
│   ├── database/mongo_store.py
│   ├── state/state_service.py # 结构化状态存储服务
│   ├── state/skill_recorder.py
│   ├── state/session_adapters.py
│   ├── rss/feed_service.py
│   ├── rss/rss_scheduler.py
│   ├── ai/chat_service.py
│   ├── static/static_files.py
│   ├── static/archive_service.py
│   └── storage/oss_client.py
└── cli/
    └── state_query.py  # 状态查询 CLI
```

## 执行准则

1. **源码只读** — 除非 `/rui code` 命令明确指定，否则只读源码进行分析
2. **分支隔离** — 故事实现必须在 `feat/YiAi-<name>` 分支上进行
3. **测试先行** — 无测试文件前不修改源码（本仓库当前无测试框架，需引入 pytest）
4. **P0 清零** — 每个模块完成后必须通过安全/P0 检查
5. **文档同步** — 代码变更后必须同步更新 `docs/故事任务面板/` 下的故事文档
6. **配置驱动** — 所有设置通过 `config.yaml` 或环境变量覆盖，不硬编码
7. **路径安全** — 文件操作必须通过 `_validate_path` / `_resolve_static_path` 做路径遍历防护
8. **错误一致** — 所有异常通过 `BusinessException` + `ErrorCode` 枚举抛出

## 退化对策

| 场景 | 处理方式 |
|------|---------|
| MongoDB 不可用 | 初始化失败，抛出异常，应用无法启动 |
| OSS 不可用 | 降级到本地存储（upload.py:147） |
| Observer 组件不可用 | 跳过注册，仅打印 warning |
| Token 缺失 | 降级跳过认证，打印日志 |
| RSS 系统失败 | 不阻断服务器启动 |
| 脚本执行超时 | 杀死进程，返回错误信息 |

## 项目约束

- Python 3.10+（推断自类型注解语法）
- MongoDB 4.x+
- 不使用 ORM — 直接通过 motor 访问 MongoDB
- 异步优先 — 所有 I/O 操作用 async/await
- src-layout — 源码在 `src/` 下，非包代码在根目录

<!-- rui:project-start -->
YiAi — FastAPI 后端服务，MongoDB + motor 异步驱动，config.yaml + pydantic-settings 配置。版本 1.0.0，仓库 git@github.com:effiy/YiAi.git，src-layout 单体架构。
<!-- rui:project-end -->
