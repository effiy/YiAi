from datetime import datetime
from typing import Any, Optional
from functools import wraps
import logging
from database import db

# 配置日志记录器
logger = logging.getLogger(__name__)

def ensure_initialized():
    """确保数据库已初始化的装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not hasattr(db, '_initialized') or not db._initialized:
                logger.info("Initializing database connection")
                await db.initialize()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def is_valid_date(date_str: str) -> bool:
    """检查字符串是否为有效日期格式"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False

def is_number(value: Any) -> bool:
    """检查值是否为数字"""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

def create_response(code: int, message: str, data: Any = None) -> dict:
    """统一的响应格式"""
    return {
        "code": code,
        "message": message,
        "data": data
    }

def handle_error(e: Exception, status_code: int = 500) -> dict:
    """统一的错误处理"""
    logger.error(f"Error occurred: {str(e)}")
    return create_response(
        code=status_code,
        message=str(e),
        data=None
    ) 