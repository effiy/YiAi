"""自定义异常定义"""
from typing import Any, Optional
from core.error_codes import ErrorCode

class BusinessException(Exception):
    """
    业务逻辑异常
    主动抛出此异常时，会被全局异常处理器捕获并返回标准错误响应
    """
    def __init__(
        self, 
        error_code: ErrorCode, 
        message: Optional[str] = None, 
        data: Any = None
    ):
        self.error_code = error_code
        self.message = message or error_code.message
        self.data = data
        super().__init__(self.message)
