"""统一响应格式工具"""
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional


def success_response(
    data: Any = None,
    message: str = "操作成功",
    **kwargs
) -> JSONResponse:
    """创建成功响应"""
    content: Dict[str, Any] = {
        "success": True,
        "message": message,
        **kwargs
    }
    if data is not None:
        content["data"] = data
    return JSONResponse(status_code=200, content=content)


def error_response(
    message: str,
    status_code: int = 500,
    detail: Optional[str] = None,
    **kwargs
) -> JSONResponse:
    """创建错误响应"""
    content: Dict[str, Any] = {
        "success": False,
        "message": message,
        "detail": detail or message,
        **kwargs
    }
    return JSONResponse(status_code=status_code, content=content)


def list_response(
    items: list,
    message: Optional[str] = None,
    **kwargs
) -> JSONResponse:
    """创建列表响应"""
    content: Dict[str, Any] = {
        "success": True,
        "count": len(items),
        **kwargs
    }
    
    # 根据上下文决定使用 sessions 还是其他字段名
    if "sessions" not in kwargs:
        content["sessions"] = items
    
    if message:
        content["message"] = message
    else:
        content["message"] = f"获取到 {len(items)} 个会话"
    
    return JSONResponse(status_code=200, content=content)

