import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import base, oss, mysql, mongodb

# 禁用 Python 字节码缓存
sys.dont_write_bytecode = True

# 确保子进程也不生成 __pycache__
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

app = FastAPI(
    title="FastAPI Server",
    description="FastAPI 服务器",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    # 在生产环境中应该设置具体的域名
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# 注册路由
app.include_router(base.router)
app.include_router(oss.router)
app.include_router(mysql.router)
app.include_router(mongodb.router)

def start():
    import uvicorn
    uvicorn.run(
        "apiServer:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 启用热加载
    )

if __name__ == "__main__":
    start()