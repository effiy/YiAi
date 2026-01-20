"""应用入口与生命周期管理
- 负责应用启动/关闭流程、路由动态注册、CORS 和认证中间件配置
- 作为启动脚本直接运行
"""
import logging
import uvicorn
import os
import sys
from contextlib import asynccontextmanager

# 设置字节码生成和路径
sys.dont_write_bytecode = True
sys.path.append(os.getcwd())

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from core.database import db
from core.settings import settings
from core.middleware import header_verification_middleware
from core.logger import setup_logging
from core.exception_handler import register_exception_handlers
from api.routes import debug, upload, execution, wework

# 导入服务模块
from services.rss.rss_scheduler import init_rss_system, shutdown_rss_system

logger = logging.getLogger(__name__)


def _build_lifespan(init_db: bool, init_rss: bool):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        应用生命周期管理
        """
        logger.info("正在启动应用...")
        try:
            if init_db and settings.startup_init_database:
                await db.initialize()
                logger.info("数据库初始化成功")
            if init_rss and settings.startup_init_rss_system:
                init_rss_system()
            logger.info("应用启动完成")
        except Exception as e:
            logger.error(f"应用启动失败: {str(e)}", exc_info=True)
            raise

        yield

        logger.info("正在关闭应用...")
        try:
            if init_rss and settings.startup_init_rss_system:
                shutdown_rss_system()
            if init_db and settings.startup_init_database:
                await db.close()
            logger.info("应用关闭完成")
        except Exception as e:
            logger.error(f"应用关闭时出错: {str(e)}", exc_info=True)
    return lifespan


def create_app(
    *,
    enable_auth: bool | None = None,
    init_db: bool | None = None,
    init_rss: bool | None = None,
) -> FastAPI:
    """
    创建 FastAPI 应用实例
    """
    # 配置日志
    setup_logging()

    auth_enabled = enable_auth if enable_auth is not None else settings.middleware_auth_enabled
    db_init_enabled = init_db if init_db is not None else True
    rss_init_enabled = init_rss if init_rss is not None else True

    app = FastAPI(
        title="YiAi API",
        description="YiPet AI 服务 API",
        version="1.0.0",
        lifespan=_build_lifespan(db_init_enabled, rss_init_enabled)
    )

    # 注册全局异常处理器
    register_exception_handlers(app)

    # 注册 API 路由
    app.include_router(debug.router, tags=["Debug"])
    app.include_router(upload.router, tags=["Upload"])
    app.include_router(execution.router, tags=["Execution"])
    app.include_router(wework.router, tags=["WeWork"])

    origins = settings.get_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=(origins != ["*"]),
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=3600,
    )
    logger.info(f"CORS 配置: 已启用, Origins: {origins}")

    if auth_enabled:
        app.middleware("http")(header_verification_middleware)
        logger.info("认证中间件已启用")
    else:
        logger.info("认证中间件已禁用")

    # 挂载静态文件
    app.mount("/static", StaticFiles(directory="static"), name="static")

    return app

# 默认应用实例（用于生产运行与兼容现有导入）
app = create_app()

if __name__ == "__main__":
    # 从配置获取
    host = settings.server_host
    port = settings.server_port
    reload = settings.server_reload

    print(f"正在启动服务器: http://{host}:{port}")
    print(f"自动重载: {'启用' if reload else '禁用'}")

    # 获取 uvicorn 配置参数
    log_level = settings.logging_level.lower()
    limit_concurrency = settings.uvicorn_limit_concurrency
    limit_max_requests = settings.uvicorn_limit_max_requests
    timeout_keep_alive = settings.uvicorn_timeout_keep_alive

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        limit_concurrency=limit_concurrency,
        limit_max_requests=limit_max_requests,
        timeout_keep_alive=timeout_keep_alive
    )
