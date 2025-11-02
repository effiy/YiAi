import sys, os

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import logging

from router import base, mongodb, oss, prompt, mem0, qdrant, session, dataSync

# 禁用 Python 字节码缓存
sys.dont_write_bytecode = True

# 确保子进程也不生成 __pycache__
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用实例
app = FastAPI(
    title="YiAi API",
    description="AI服务API",
    version="1.0.0",
    docs_url="/docs"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境中应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有头部
)

# 中间件开关，通过环境变量控制
ENABLE_MIDDLEWARE = True

# 中间件拦截器
@app.middleware("http")
async def header_verification_middleware(request: Request, call_next):
    try:
        # 记录请求信息
        logger.info(f"收到请求: {request.method} {request.url}")
        
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
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Invalid or missing headers",
                    "message": "请提供有效的X-Token和X-User请求头"
                },
            )

        response = await call_next(request)
        logger.info(f"请求处理完成: {request.method} {request.url}")
        return response
        
    except Exception as e:
        logger.error(f"中间件处理异常: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误", "message": "中间件处理异常"}
        )

# 全局异常处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"请求验证错误: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "请求参数验证失败",
            "message": "请检查请求参数格式",
            "errors": exc.errors(),
            "status": 422
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP异常: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "message": exc.detail,
            "status": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误",
            "message": "服务器处理请求时发生未知错误",
            "status": 500
        }
    )

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
            "base": "/clients/base.html",
            "mem0": "/clients/mem0Client.html",
            "qdrant": "/clients/qdrantClient.html"
        }
    }

app.include_router(oss.router)
app.include_router(base.router)
app.include_router(prompt.router)
app.include_router(mongodb.router)
app.include_router(mem0.router)
app.include_router(qdrant.router)
app.include_router(session.router)
app.include_router(dataSync.router)

# 当直接运行此脚本时执行以下代码
if __name__ == "__main__":
    # 导入uvicorn服务器
    import uvicorn
    # 启动uvicorn服务器，运行FastAPI应用
    # host="0.0.0.0" 允许外网访问
    uvicorn.run(
        "server:app",  # 指定应用模块路径
        host="0.0.0.0",  # 允许外网访问
        port=8000,       # 可根据需要修改端口
        reload=True      # 启用热重载，便于开发调试
    )
