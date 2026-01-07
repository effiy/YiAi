"""全局异常处理器"""
import logging
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from core.error_codes import ErrorCode, map_http_to_error_code
from core.response import fail
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理请求参数验证错误"""
    error_details = exc.errors()
    error_messages = []
    
    for error in error_details:
        # 获取字段路径
        loc = error.get("loc", [])
        field = ".".join(str(l) for l in loc if l not in ('body', 'query', 'path'))
        msg = error.get("msg", "验证失败")
        error_messages.append(f"{field}: {msg}" if field else msg)
    
    error_msg = "; ".join(error_messages)
    logger.warning(f"参数验证失败: {error_msg} | URL: {request.url}")
    
    return fail(
        error=ErrorCode.INVALID_PARAMS,
        message=f"参数验证失败: {error_msg}",
        data=error_details
    )

async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """处理业务逻辑异常"""
    logger.warning(f"业务异常: {exc.message} | Code: {exc.error_code.business}")
    return fail(
        error=exc.error_code,
        message=exc.message,
        data=exc.data
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """处理 FastAPI 抛出的 HTTP 异常"""
    logger.warning(f"HTTP异常: {exc.detail} | Status: {exc.status_code}")
    
    # 尝试映射到自定义错误码
    error_code = map_http_to_error_code(exc.status_code)
    
    return fail(
        error=error_code,
        message=str(exc.detail),
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理未捕获的全局异常"""
    logger.error(f"未处理的系统异常: {str(exc)}", exc_info=True)
    return fail(
        error=ErrorCode.SERVER_ERROR,
        message="服务器内部错误，请联系管理员"
    )

def register_exception_handlers(app):
    """注册所有异常处理器"""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
