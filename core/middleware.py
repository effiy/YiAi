"""认证中间件 - 处理请求头验证"""
import os
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from core.config import settings
from core.response import fail
from core.error_codes import ErrorCode


logger = logging.getLogger(__name__)

def _add_cors_headers(response: JSONResponse, request: Request) -> JSONResponse:
    """
    为响应添加 CORS 头（允许所有来源）
    
    Args:
        response: 原始响应对象
        request: 请求对象
        
    Returns:
        JSONResponse: 包含 CORS 头的响应对象
        
    Example:
        >>> response = _add_cors_headers(JSONResponse({}), request)
        >>> response.headers["Access-Control-Allow-Origin"]
        '*'
    """
    # 默认允许所有来源，与 server.py 中的 CORS 配置保持一致
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "3600"

    return response


async def header_verification_middleware(request: Request, call_next):
    """
    请求头验证中间件
    验证 X-Token 请求头（如果配置了环境变量）
    
    Args:
        request: 请求对象
        call_next: 下一个中间件/处理函数
        
    Returns:
        Response: 响应对象
        
    Example:
        >>> # 在 FastAPI 应用中注册
        >>> app.add_middleware(header_verification_middleware)
    """
    try:
        # 记录请求信息
        content_type = request.headers.get("content-type", "")
        logger.info(f"收到请求: {request.method} {request.url}, Content-Type: {content_type}")

        # 跳过 OPTIONS 预检请求，让 CORS 中间件处理
        if request.method == "OPTIONS":
            response = await call_next(request)
            return response

        # 检查中间件是否启用
        enable_middleware = settings.is_auth_middleware_enabled()
        if not enable_middleware:
            response = await call_next(request)
            return response

        # 获取配置
        required_token = settings.auth_token

        # 如果未配置token，跳过验证
        if not required_token:
            logger.info("未配置API验证，跳过请求头验证")
            response = await call_next(request)
            return response

        x_token = request.headers.get("X-Token", "")

        # 验证请求头
        if x_token != required_token:
            logger.warning(f"无效的请求头: X-Token={x_token}")
            error_response = fail(
                error=ErrorCode.UNAUTHORIZED,
                message="Invalid or missing headers"
            )
            # 添加 CORS 头
            return _add_cors_headers(error_response, request)

        response = await call_next(request)
        logger.info(f"请求处理完成: {request.method} {request.url}")
        return response

    except Exception as e:
        logger.error(f"中间件处理异常: {str(e)}", exc_info=True)
        error_response = fail(
            error=ErrorCode.SERVER_ERROR,
            message="Internal Server Error"
        )
        return _add_cors_headers(error_response, request)

