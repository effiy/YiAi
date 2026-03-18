# 项目目录结构

```
YiAi/
├── main.py                          # 🚀 兼容性入口文件
├── config.yaml                      # ⚙️ 主配置文件
├── requirements.txt                 # 📦 Python 依赖
├── CLAUDE.md                        # 📖 Claude Code 项目说明
├── .gitignore                       # 🙈 Git 忽略文件
│
├── docs/                            # 📚 文档目录
│   └── structure.md                 # 🗂️ 本文档 - 目录结构说明
│
├── logs/                            # 📝 日志目录
│
└── src/                             # 💻 源代码目录
    ├── main.py                      # 🎯 FastAPI 应用入口（应用工厂）
    │
    ├── api/                         # 🌐 API 层
    │   └── routes/                  # 🛣️ API 路由
    │       ├── execution.py         # ⚡ 动态模块执行端点
    │       ├── upload.py            # 📤 文件上传端点
    │       ├── wework.py            # 💼 企业微信集成端点
    │       └── maintenance.py       # 🔧 维护端点
    │
    ├── core/                        # 🏗️ 核心基础设施
    │   ├── config.py                # 🔧 配置管理（YAML + 环境变量）
    │   ├── database.py              # 🗄️ MongoDB 单例
    │   ├── logger.py                # 📋 日志设置
    │   ├── exceptions.py            # ⚠️ 自定义异常
    │   ├── error_codes.py           # 🔢 错误码定义
    │   ├── response.py              # 📨 统一响应格式
    │   ├── middleware.py            # 🛡️ 认证中间件
    │   └── exception_handler.py     # 🚨 全局异常处理器
    │
    ├── models/                      # 📊 数据模型
    │   └── schemas.py               # 📐 Pydantic 模型定义
    │
    └── services/                    # ⚙️ 业务逻辑层
        ├── execution/               # 🔌 模块执行引擎
        │   └── executor.py          # 🎮 模块执行器
        │
        ├── rss/                     # 📰 RSS 源管理
        │   ├── scheduler.py         # ⏰ RSS 调度器
        │   └── parser.py            # 📝 RSS 解析器
        │
        ├── ai/                      # 🤖 AI 聊天服务
        │   └── ollama_client.py     # 🧠 Ollama 客户端
        │
        ├── storage/                 # 💾 存储服务
        │   └── oss_client.py        # ☁️ OSS 存储客户端
        │
        ├── static/                  # 📁 静态文件服务
        │   └── file_manager.py      # 🗃️ 文件管理器
        │
        └── database/                # 🗄️ 数据访问层
            └── crud.py              # 📝 通用 CRUD 操作
```
