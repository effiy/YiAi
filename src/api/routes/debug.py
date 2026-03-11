from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/debug", include_in_schema=False)
async def debug_page():
    """
    API 调试页面
    """
    return FileResponse("static/index.html")
