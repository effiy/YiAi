import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import db
from config import Config
from middleware.auth import header_verification_middleware
from constants import DEFAULT_HOST, DEFAULT_PORT, UVICORN_RELOAD

# 导入所有路由
from router import base
from router import prompt
from router import oss
from router import rss
from router import session
from router import mongodb
from router import dataSync
from router import apiRequest

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建配置实例
config = Config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("正在启动应用...")
    try:
        # 初始化数据库
        await db.initialize()
        logger.info("数据库初始化成功")

        # 如果启用了 RSS 定时任务，启动调度器
        if config.is_rss_scheduler_enabled():
            try:
                from router.rss import start_rss_scheduler
                start_rss_scheduler()
                logger.info("RSS 定时任务已启动")
            except Exception as e:
                logger.warning(f"启动 RSS 定时任务失败: {str(e)}")

        logger.info("应用启动完成")
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}", exc_info=True)
        raise

    yield

    # 关闭时执行
    logger.info("正在关闭应用...")
    try:
        # 关闭 RSS 定时任务
        if config.is_rss_scheduler_enabled():
            try:
                from router.rss import stop_rss_scheduler
                stop_rss_scheduler()
                logger.info("RSS 定时任务已停止")
            except Exception as e:
                logger.warning(f"停止 RSS 定时任务失败: {str(e)}")

        # 关闭数据库连接
        await db.close()
        logger.info("应用关闭完成")
    except Exception as e:
        logger.error(f"应用关闭时出错: {str(e)}", exc_info=True)


# 创建 FastAPI 应用
app = FastAPI(
    title="YiAi API",
    description="YiPet AI 服务 API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS - 允许所有跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=False,  # 使用 "*" 时 credentials 必须为 False
    allow_methods=["*"],  # 允许所有 HTTP 方法 (GET, POST, PUT, DELETE, OPTIONS 等)
    allow_headers=["*"],  # 允许所有请求头
    expose_headers=["*"],  # 暴露所有响应头给客户端
    max_age=3600,  # 预检请求缓存时间（秒）
)
logger.info("CORS 配置: 已启用，允许所有来源")

# 添加认证中间件
if config.is_auth_middleware_enabled():
    app.middleware("http")(header_verification_middleware)
    logger.info("认证中间件已启用")
else:
    logger.info("认证中间件已禁用")

# 注册所有路由
app.include_router(base.router)
app.include_router(prompt.router)

app.include_router(session.router)
app.include_router(oss.router)
app.include_router(apiRequest.router)
app.include_router(mongodb.router)
app.include_router(dataSync.router)
app.include_router(rss.router)

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return JSONResponse(content={
        "message": "YiAi API 服务运行中",
        "version": "1.0.0"
    })

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return JSONResponse(content={
        "status": "healthy"
    })


if __name__ == "__main__":
    import uvicorn

    # 从环境变量获取配置
    host = os.getenv("HOST", DEFAULT_HOST)
    port = int(os.getenv("PORT", DEFAULT_PORT))
    reload = UVICORN_RELOAD

    logger.info(f"正在启动服务器: http://{host}:{port}")
    logger.info(f"自动重载: {'启用' if reload else '禁用'}")

    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )





