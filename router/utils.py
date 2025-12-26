"""统一的响应和错误处理工具"""
from typing import Any, Dict, Optional
from fastapi.responses import JSONResponse
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
import logging

logger = logging.getLogger(__name__)


def create_response(code: int, message: str, data: Any = None) -> dict:
    """创建统一的响应格式（字典形式）"""
    return {
        "code": code,
        "message": message,
        "data": data
    }


def handle_error(e: Exception, status_code: int = 500) -> dict:
    """统一的错误处理（返回字典）"""
    error_msg = str(e)
    logger.error(f"发生错误: {error_msg}")
    return create_response(
        code=status_code,
        message=error_msg,
        data=None
    )


def success_response(
    data: Any = None,
    message: str = "操作成功",
    **kwargs
) -> JSONResponse:
    """创建成功响应（JSONResponse）"""
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
    """创建错误响应（JSONResponse）"""
    content: Dict[str, Any] = {
        "success": False,
        "message": message,
        "detail": detail or message,
        **kwargs
    }
    return JSONResponse(status_code=status_code, content=content)


def create_error_response(
    status_code: int,
    detail: str,
    message: str = None,
    errors: list = None,
    code: int = None
) -> JSONResponse:
    """创建统一的错误响应格式（用于异常处理）"""
    content: Dict[str, Any] = {
        "detail": detail,
        "message": message or detail,
        "msg": message or detail,
        "status": status_code,
        "code": code or status_code
    }
    
    if errors is not None:
        content["errors"] = errors
    
    return JSONResponse(status_code=status_code, content=content)


def resp_ok(*, data: Any = None, pagination: dict = None, msg: str = "success") -> JSONResponse:
    """RespOk的替代函数（兼容旧代码）"""
    return JSONResponse(
        status_code=http_status.HTTP_200_OK,
        content=jsonable_encoder({
            'status': 200,
            'code': 200,
            'msg': msg,
            'data': data,
            'pagination': pagination
        })
    )


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
