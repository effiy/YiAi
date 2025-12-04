import sys, os

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import logging

from router import base, mongodb, oss, prompt, session, dataSync, rss, apiRequest
from contextlib import asynccontextmanager

# 禁用 Python 字节码缓存
sys.dont_write_bytecode = True

# 确保子进程也不生成 __pycache__
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的生命周期管理"""
    # 启动时执行
    logger.info("应用启动中...")
    
    # 启动 RSS 定时解析任务
    try:
        # 检查是否启用定时任务（通过环境变量控制）
        enable_rss_scheduler = os.getenv("ENABLE_RSS_SCHEDULER", "true").lower() == "true"
        if enable_rss_scheduler:
            rss.start_rss_scheduler()
            logger.info("RSS 定时解析任务已启动")
        else:
            logger.info("RSS 定时解析任务已禁用（通过环境变量）")
    except Exception as e:
        logger.warning(f"启动 RSS 定时解析任务失败: {str(e)}")
    
    yield
    
    # 关闭时执行
    logger.info("应用关闭中...")
    try:
        rss.stop_rss_scheduler()
        logger.info("RSS 定时解析任务已停止")
    except Exception as e:
        logger.warning(f"停止 RSS 定时解析任务失败: {str(e)}")

# 创建FastAPI应用实例
app = FastAPI(
    title="YiAi API",
    description="AI服务API",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan
)

# 中间件开关，通过环境变量控制
ENABLE_MIDDLEWARE = True

# 中间件拦截器（需要在 CORS 之前添加，以便 CORS 可以处理所有响应）
@app.middleware("http")
async def header_verification_middleware(request: Request, call_next):
    try:
        # 记录请求信息
        content_type = request.headers.get("content-type", "")
        logger.info(f"收到请求: {request.method} {request.url}, Content-Type: {content_type}")
        
        # 跳过 OPTIONS 预检请求，让 CORS 中间件处理
        if request.method == "OPTIONS":
            response = await call_next(request)
            return response
        
        # 如果中间件被禁用，直接通过
        if not ENABLE_MIDDLEWARE:
            response = await call_next(request)
            return response

        # 获取环境变量中的配置
        required_token = os.getenv("API_X_TOKEN", "")
        required_user = os.getenv("API_X_USER", "")
        
        # 如果环境变量未设置，跳过验证
        if not required_token and not required_user:
            logger.info("未配置API验证，跳过请求头验证")
            response = await call_next(request)
            return response

        x_token = request.headers.get("X-Token", "")
        x_user = request.headers.get("X-User", "")

        # 验证请求头
        token_valid = not required_token or x_token == required_token
        user_valid = not required_user or x_user == required_user
        
        if not (token_valid and user_valid):
            logger.warning(f"无效的请求头: X-Token={x_token}, X-User={x_user}")
            # 创建响应并添加 CORS 头
            response = JSONResponse(
                status_code=401,
                content={
                    "detail": "Invalid or missing headers",
                    "message": "请提供有效的X-Token和X-User请求头"
                },
            )
            # 添加 CORS 头
            origin = request.headers.get("origin")
            if origin:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "*"
                response.headers["Access-Control-Allow-Headers"] = "*"
            return response

        response = await call_next(request)
        logger.info(f"请求处理完成: {request.method} {request.url}")
        return response
        
    except Exception as e:
        logger.error(f"中间件处理异常: {str(e)}", exc_info=True)
        # 创建响应并添加 CORS 头
        response = JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误", "message": "中间件处理异常"}
        )
        # 添加 CORS 头
        origin = request.headers.get("origin")
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
        return response

# 配置 CORS 允许的来源
# 从环境变量读取，如果没有设置则使用默认值
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://effiy.cn,http://localhost:3000,http://localhost:8000").split(",")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS if origin.strip()]

# 添加 CORS 中间件（在自定义中间件之前添加，确保所有响应都包含 CORS 头）
# 注意：FastAPI 中间件执行顺序是后添加的先执行（LIFO），所以先添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有头部
    expose_headers=["*"],  # 暴露所有头部
)

# 全局异常处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"请求验证错误: {exc}")
    error_details = exc.errors()
    error_messages = []
    for error in error_details:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg", "验证失败")
        error_messages.append(f"{field}: {msg}")
    
    error_msg = "请求参数验证失败: " + "; ".join(error_messages)
    response = JSONResponse(
        status_code=422,
        content={
            "detail": error_msg,
            "message": error_msg,
            "msg": error_msg,
            "errors": error_details,
            "status": 422,
            "code": 422
        }
    )
    # 确保异常响应也包含 CORS 头
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP异常: {exc.detail}")
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "message": exc.detail,
            "msg": exc.detail,
            "status": exc.status_code,
            "code": exc.status_code
        }
    )
    # 确保异常响应也包含 CORS 头
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误",
            "message": "服务器处理请求时发生未知错误",
            "status": 500
        }
    )
    # 确保异常响应也包含 CORS 头
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# 挂载静态文件服务（客户端 HTML 文件）
try:
    import os
    clients_dir = os.path.join(os.path.dirname(__file__), "clients")
    if os.path.exists(clients_dir):
        app.mount("/clients", StaticFiles(directory=clients_dir, html=True), name="clients")
        logger.info(f"静态文件服务已挂载: /clients -> {clients_dir}")
except Exception as e:
    logger.warning(f"挂载静态文件服务失败: {e}")

# 根路径端点
@app.get("/")
async def root():
    return {
        "message": "Welcome to YiAi API",
        "version": "1.0.0",
        "docs": "/docs",
        "clients": {
            "prompt": "/clients/prompt.html",
            "mongodb": "/clients/mongodb.html",
            "oss": "/clients/oss.html",
            "base": "/clients/base.html"
        }
    }

app.include_router(oss.router)
app.include_router(base.router)
app.include_router(prompt.router)
app.include_router(mongodb.router)
app.include_router(session.router)
app.include_router(dataSync.router)
app.include_router(rss.router)
app.include_router(apiRequest.router)

# 当直接运行此脚本时执行以下代码
if __name__ == "__main__":
    # 导入uvicorn服务器
    import uvicorn
    # 启动uvicorn服务器，运行FastAPI应用
    # host="0.0.0.0" 允许外网访问
    # 注意：如果使用 nginx 等反向代理，需要在 nginx 配置中设置 client_max_body_size
    # 例如：client_max_body_size 50M;
    uvicorn.run(
        "server:app",  # 指定应用模块路径
        host="0.0.0.0",  # 允许外网访问
        port=8000,       # 可根据需要修改端口
        reload=True,        # 启用热重载，便于开发调试
        limit_concurrency=1000,  # 最大并发连接数
        limit_max_requests=10000,  # 最大请求数（防止内存泄漏）
        timeout_keep_alive=5,  # Keep-alive 超时时间
    )




