import sys, os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from router import base, mongodb, oss, prompt

# 禁用 Python 字节码缓存
sys.dont_write_bytecode = True

# 确保子进程也不生成 __pycache__
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# 创建FastAPI应用实例
app = FastAPI()

# 添加CORS中间件，允许本地开发常用端口跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境建议设置具体域名
    allow_credentials=True,  # 允许携带认证信息
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],  # 允许的HTTP方法
    allow_headers=["*"],  # 允许所有请求头
    expose_headers=["*"],  # 允许浏览器访问的响应头
    max_age=86400,  # 预检请求缓存时间（秒）
)

# 添加额外的CORS处理中间件
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    # 处理CORS预检请求
    if request.method == "OPTIONS":
        response = await call_next(request)
        # 确保OPTIONS请求返回正确的CORS头
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response
    
    response = await call_next(request)
    return response

# 中间件开关，通过环境变量控制
ENABLE_MIDDLEWARE = True

# 中间件拦截器
@app.middleware("http")
async def header_verification_middleware(request: Request, call_next):
    # 对于CORS预检请求，直接放行
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response
    
    # 如果中间件被禁用，直接通过
    if not ENABLE_MIDDLEWARE:
        response = await call_next(request)
        return response

    x_token = request.headers.get("X-Token")
    x_client = request.headers.get("X-Client")

    # 只允许符合特定 header 的请求通过
    if x_token != os.getenv("API_X_TOKEN", "") or x_client != os.getenv("API_X_CLIENT", ""):
        return JSONResponse(
            status_code=403,
            content={"detail": "Invalid or missing headers"},
        )

    response = await call_next(request)
    return response

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
