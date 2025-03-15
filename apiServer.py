from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import base, oss

app = FastAPI(
    title="FastAPI Server",
    description="FastAPI 服务器",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(base.router)
app.include_router(oss.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)