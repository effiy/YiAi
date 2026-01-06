"""统一的响应和错误处理工具"""
from typing import Any, Dict, Optional, Union
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
import logging
from core.error_codes import (
    INVALID_PARAMS,
    DATA_NOT_FOUND, SERVER_ERROR, map_http_to_error_code
)

logger = logging.getLogger(__name__)


def create_response(code: int, message: str, data: Any = None) -> dict:
    """
    创建统一的响应格式（字典形式）
    
    Args:
        code: 状态码
        message: 消息文本
        data: 数据载荷 (可选)
        
    Returns:
        dict: 响应字典
        
    Example:
        >>> create_response(200, "Success", {"id": 1})
        {'code': 200, 'message': 'Success', 'data': {'id': 1}}
    """
    return {
        "code": code,
        "message": message,
        "data": data
    }


def handle_error(e: Exception, status_code: int = None) -> JSONResponse:
    """
    统一的错误处理（返回JSONResponse，确保状态码与业务码规范化）
    
    Args:
        e: 异常对象
        status_code: 指定的 HTTP 状态码 (可选)
        
    Returns:
        JSONResponse: 格式化的错误响应
        
    Example:
        >>> try:
        ...     raise ValueError("Invalid input")
        ... except Exception as e:
        ...     response = handle_error(e)
    """
    error_msg = str(e)
    logger.error(f"发生错误: {error_msg}")
    if isinstance(e, HTTPException):
        http_code = e.status_code
        err_code = map_http_to_error_code(http_code)
        return create_error_response(
            status_code=http_code,
            detail=e.detail if hasattr(e, 'detail') else error_msg,
            message=err_code.message,
            business_code=err_code.business
        )
    if "未找到" in error_msg or "不存在" in error_msg:
        err_code = DATA_NOT_FOUND
        return create_error_response(
            status_code=err_code.http,
            detail=error_msg,
            message=err_code.message,
            business_code=err_code.business
        )
    if isinstance(e, ValueError):
        err_code = INVALID_PARAMS
        return create_error_response(
            status_code=err_code.http,
            detail=error_msg,
            message=err_code.message,
            business_code=err_code.business
        )
    err_code = SERVER_ERROR
    return create_error_response(
        status_code=err_code.http,
        detail=error_msg,
        message=err_code.message,
        business_code=err_code.business
    )


def success_response(
    data: Any = None,
    message: str = "操作成功",
    **kwargs
) -> JSONResponse:
    """
    创建成功响应（JSONResponse）
    
    Args:
        data: 响应数据
        message: 成功消息
        **kwargs: 其他附加字段
        
    Returns:
        JSONResponse: 成功响应对象
        
    Example:
        >>> response = success_response({"id": 1})
        >>> response.status_code
        200
    """
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
    """
    创建错误响应（JSONResponse）
    
    Args:
        message: 错误消息
        status_code: HTTP 状态码
        detail: 详细错误信息
        **kwargs: 其他附加字段
        
    Returns:
        JSONResponse: 错误响应对象
        
    Example:
        >>> response = error_response("Internal Error", status_code=500)
        >>> response.status_code
        500
    """
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
    code: int = None,
    business_code: int = None
) -> JSONResponse:
    """
    构建标准错误响应 JSONResponse
    
    Args:
        status_code: HTTP 状态码
        detail: 详细错误信息
        message: 简短错误消息 (可选)
        errors: 错误列表详情 (可选)
        code: 兼容旧版错误码 (可选)
        business_code: 业务错误码 (可选)
    Example:
        >>> response = create_error_response(404, "Not Found", business_code=404001)
        >>> response.status_code
        404
    """
    content = {
        "success": False,
        "detail": detail,
        "message": message or detail
    }
    
    if errors:
        content["errors"] = errors
        
    if business_code is not None:
        content["business_code"] = business_code
        content["code"] = business_code  # 兼容字段
    elif code is not None:
        content["code"] = code
        
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(content)
    )

def create_legacy_success_response(data: Union[list, dict, str] = None, pagination: dict = None, message: str = "success") -> JSONResponse:
    """
    兼容旧版响应格式的成功响应
    """
    return success_response(data=data, message=message, pagination=pagination)

