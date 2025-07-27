import sys, os

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

from router import base, mongodb, oss, prompt

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
    docs_url="/docs",
    redoc_url="/redoc"
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

        x_token = request.headers.get("X-Token")
        x_client = request.headers.get("X-Client")

        # 只允许符合特定 header 的请求通过
        if x_token != os.getenv("API_X_TOKEN", "") or x_client != os.getenv("API_X_CLIENT", ""):
            logger.warning(f"无效的请求头: X-Token={x_token}, X-Client={x_client}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid or missing headers"},
            )

        response = await call_next(request)
        logger.info(f"请求处理完成: {request.method} {request.url}")
        return response
        
    except Exception as e:
        logger.error(f"中间件处理异常: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误"}
        )

# 全局异常处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"请求验证错误: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": "请求参数验证失败", "errors": exc.errors()}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP异常: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"}
    )

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "YiAi API is running"}

# 根路径端点
@app.get("/")
async def root():
    return {"message": "Welcome to YiAi API", "docs": "/docs"}

app.include_router(oss.router)
app.include_router(base.router)
app.include_router(prompt.router)
app.include_router(mongodb.router)

# 当直接运行此脚本时执行以下代码
if __name__ == "__main__":
    # 导入uvicorn服务器
    import uvicorn
    # 启动uvicorn服务器，运行FastAPI应用
    uvicorn.run(
        "server:app",  # 指定应用模块路径
        reload=True    # 启用热重载，便于开发调试
    )
