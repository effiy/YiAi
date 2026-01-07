"""应用入口与生命周期管理
- 负责应用启动/关闭流程、路由动态注册、CORS 和认证中间件配置
- 作为启动脚本直接运行
"""
import logging
import uvicorn
import os
import sys
import shutil
import base64
from contextlib import asynccontextmanager

# 设置字节码生成和路径
sys.dont_write_bytecode = True
sys.path.append(os.getcwd())

from fastapi import FastAPI, Query, UploadFile, File, Form, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from core.database import db
from core.config import Config, settings
from core.middleware import header_verification_middleware
from core.schemas import ExecuteRequest, FileUploadRequest
from core.logger import setup_logging
from core.exception_handler import register_exception_handlers
from core.response import success

# 导入服务模块
from services.rss.rss_scheduler import init_rss_system, shutdown_rss_system
from services.execution.executor import execute_module

logger = logging.getLogger(__name__)


def _build_lifespan(config: Config, init_db: bool, init_rss: bool):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        应用生命周期管理
        
        Args:
            app: FastAPI 应用实例
            
        Yields:
            None
            
        Example:
            >>> async with lifespan(app):
            ...     pass
        """
        logger.info("正在启动应用...")
        try:
            if init_db and config.is_startup_init_database_enabled():
                await db.initialize()
                logger.info("数据库初始化成功")
            if init_rss and config.is_startup_init_rss_enabled():
                init_rss_system()
            logger.info("应用启动完成")
        except Exception as e:
            logger.error(f"应用启动失败: {str(e)}", exc_info=True)
            raise

        yield

        logger.info("正在关闭应用...")
        try:
            if init_rss and config.is_startup_init_rss_enabled():
                shutdown_rss_system()
            if init_db and config.is_startup_init_database_enabled():
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
    config: Config | None = None
) -> FastAPI:
    """
    创建 FastAPI 应用实例
    
    Args:
        enable_auth: 是否启用鉴权中间件
        init_db: 是否初始化数据库
        init_rss: 是否初始化 RSS 系统
        config: 配置对象
        
    Returns:
        FastAPI: 配置完成的应用实例
        
    Example:
        >>> app = create_app(enable_auth=False, init_db=False)
        >>> assert isinstance(app, FastAPI)
    """
    config = config or Config()

    # 配置日志
    setup_logging()

    auth_enabled = enable_auth if enable_auth is not None else config.is_auth_middleware_enabled()
    db_init_enabled = init_db if init_db is not None else True
    rss_init_enabled = init_rss if init_rss is not None else True

    app = FastAPI(
        title="YiAi API",
        description="YiPet AI 服务 API",
        version="1.0.0",
        lifespan=_build_lifespan(config, db_init_enabled, rss_init_enabled)
    )

    # 注册全局异常处理器
    register_exception_handlers(app)

    origins = config.get_cors_origins()
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

    @app.get("/debug", include_in_schema=False)
    async def debug_page():
        """
        API 调试页面
        """
        return FileResponse("static/index.html")

    @app.post("/upload")
    async def upload_file(
        request: FileUploadRequest
    ):
        """
        文件上传接口 (JSON 方式)
        """
        target_dir = request.target_dir
        # 确保目录存在 (相对于当前工作目录)
        save_dir = os.path.join(os.getcwd(), target_dir)
        os.makedirs(save_dir, exist_ok=True)
        
        filename = request.filename
        file_path = os.path.join(save_dir, filename)
        
        try:
            if request.is_base64:
                # Base64 解码并写入二进制文件
                content_bytes = base64.b64decode(request.content)
                with open(file_path, "wb") as f:
                    f.write(content_bytes)
            else:
                # 直接写入文本文件
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(request.content)
        except Exception as e:
            logger.error(f"文件保存失败: {str(e)}", exc_info=True)
            raise ValueError(f"文件保存失败: {str(e)}")
            
        # 返回相对路径
        rel_path = f"/{target_dir}/{filename}"
        # 统一路径分隔符
        rel_path = rel_path.replace(os.sep, '/')
        # 确保不以 // 开头 (如果 target_dir 为空或 / 开头)
        if rel_path.startswith('//'):
            rel_path = rel_path[1:]
            
        return success(data={"url": rel_path})

    @app.get("/")
    async def execute_module_get(
        module_name: str = "services.web.crawler.crawler_service",
        method_name: str = "crawl_and_extract",
        parameters: str = Query(default='{"url": "https://www.qbitai.com/"}')
    ):
        """
        GET 方式执行指定模块方法
        """
        result = await execute_module(module_name, method_name, parameters)
        return success(data=result)

    @app.post("/")
    async def execute_module_post(request: ExecuteRequest):
        """
        POST 方式执行指定模块方法
        """
        logger.info(f"执行模块: {request.module_name}, 方法: {request.method_name}")
        logger.info(f"参数: {request.parameters}")
        result = await execute_module(request.module_name, request.method_name, request.parameters)
        return success(data=result)

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

