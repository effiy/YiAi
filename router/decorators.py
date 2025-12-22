"""路由装饰器：统一处理错误和常见模式"""
import logging
from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException, Request
from router.utils import get_user_id
from modules.services.sessionService import SessionService

logger = logging.getLogger(__name__)

# 全局服务实例缓存
_session_service: SessionService | None = None


async def get_session_service() -> SessionService:
    """获取会话服务实例（懒加载）"""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
        await _session_service.initialize()
    return _session_service


def handle_route_errors(operation_name: str = "操作"):
    """
    统一处理路由错误的装饰器
    
    Args:
        operation_name: 操作名称，用于错误日志和消息
    
    Usage:
        @router.get("/example")
        @handle_route_errors("获取示例")
        async def get_example():
            # 业务逻辑
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # HTTPException 直接抛出（如404、400等）
                raise
            except ValueError as e:
                # ValueError 通常表示资源不存在，转换为404
                logger.warning(f"{operation_name}失败（资源不存在）: {str(e)}")
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                logger.error(f"{operation_name}失败: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"{operation_name}失败: {str(e)}"
                )
        return wrapper
    return decorator


def extract_user_id(func: Callable) -> Callable:
    """
    自动提取用户ID的装饰器
    从请求参数或Request对象中提取user_id并注入到函数参数中
    
    Usage:
        @router.get("/example")
        @extract_user_id
        async def get_example(http_request: Request, user_id: str = None):
            # user_id 已经被自动提取
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 查找Request对象
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            for key, value in kwargs.items():
                if isinstance(value, Request):
                    request = value
                    break
        
        # 如果找到Request对象，提取user_id
        if request:
            # 从kwargs中获取user_id（可能来自请求参数或请求体）
            user_id_param = kwargs.get('user_id')
            if 'user_id' not in kwargs or kwargs['user_id'] is None:
                # 尝试从请求体或请求参数中获取
                if hasattr(request, 'body') and hasattr(request, 'json'):
                    try:
                        body = await request.json()
                        user_id_param = body.get('user_id') if isinstance(body, dict) else None
                    except:
                        pass
            
            # 使用get_user_id统一提取
            kwargs['user_id'] = get_user_id(request, user_id_param)
        
        return await func(*args, **kwargs)
    return wrapper

