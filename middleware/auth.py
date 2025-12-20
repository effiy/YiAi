"""认证中间件 - 处理请求头验证"""
import os
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def header_verification_middleware(request: Request, call_next):
    """
    请求头验证中间件
    验证 X-Token 请求头（如果配置了环境变量）
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
        enable_middleware = os.getenv("ENABLE_AUTH_MIDDLEWARE", "true").lower() == "true"
        if not enable_middleware:
            response = await call_next(request)
            return response

        # 获取环境变量中的配置
        required_token = os.getenv("API_X_TOKEN", "")
        
        # 如果环境变量未设置，跳过验证
        if not required_token:
            logger.info("未配置API验证，跳过请求头验证")
            response = await call_next(request)
            return response

        x_token = request.headers.get("X-Token", "")

        # 验证请求头
        if x_token != required_token:
            logger.warning(f"无效的请求头: X-Token={x_token}")
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Invalid or missing headers",
                    "message": "请提供有效的X-Token请求头"
                },
            )

        response = await call_next(request)
        logger.info(f"请求处理完成: {request.method} {request.url}")
        return response
        
    except Exception as e:
        logger.error(f"中间件处理异常: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误", "message": "中间件处理异常"}
        )

