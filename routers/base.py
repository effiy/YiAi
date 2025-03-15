from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "欢迎使用 FastAPI!"}