"""统一异常处理和响应构建工具"""
import logging
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from core.utils import create_error_response

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理请求验证错误"""
    logger.error(f"请求验证错误: {exc}")
    error_details = exc.errors()
    error_messages = []
    
    for error in error_details:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg", "验证失败")
        error_messages.append(f"{field}: {msg}")
    
    error_msg = "请求参数验证失败: " + "; ".join(error_messages)
    
    return create_error_response(
        status_code=422,
        detail=error_msg,
        message=error_msg,
        errors=error_details
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """处理HTTP异常"""
    logger.error(f"HTTP异常: {exc.detail}")
    return create_error_response(
        status_code=exc.status_code,
        detail=exc.detail,
        message=exc.detail
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理未捕获的异常"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return create_error_response(
        status_code=500,
        detail="服务器内部错误",
        message="服务器处理请求时发生未知错误"
    )


