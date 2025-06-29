import sys, os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from router import base, mongodb, oss, docs

# 禁用 Python 字节码缓存
sys.dont_write_bytecode = True

# 确保子进程也不生成 __pycache__
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# 创建FastAPI应用实例
app = FastAPI()

# 中间件拦截器
@app.middleware("http")
async def header_verification_middleware(request: Request, call_next):
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

# 挂载 docs 目录为静态文件目录
app.mount("/static/docs", StaticFiles(directory="docs"), name="static_docs")

app.include_router(oss.router)
app.include_router(docs.router)
app.include_router(base.router)
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
