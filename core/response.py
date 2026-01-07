"""响应对象封装
- 定义统一的响应对象 StandardResponse
- 提供 success 和 fail 辅助函数
"""
from typing import Union, Generic, TypeVar, Optional, Any
from fastapi.responses import JSONResponse, Response
from fastapi.encoders import jsonable_encoder
from core.error_codes import ErrorCode

T = TypeVar("T")

class StandardResponse(Generic[T]):
    """
    标准响应对象
    """
    def __init__(
        self,
        code: int = 0,
        message: str = "success",
        data: Optional[T] = None,
        http_code: int = 200
    ):
        self.code = code        # 业务状态码
        self.message = message  # 提示消息
        self.data = data        # 数据载荷
        self.http_code = http_code # HTTP 状态码 (不包含在响应体中，仅用于 status_code)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }

def success(
    data: Union[list, dict, str, None] = None,
    message: str = "success",
    pagination: dict = None
) -> Response:
    """
    创建成功响应 (200 OK)
    """
    content = {
        "code": ErrorCode.OK.business,
        "message": message,
        "data": data
    }
    if pagination:
        content["pagination"] = pagination
        
    return JSONResponse(
        status_code=ErrorCode.OK.http,
        content=jsonable_encoder(content)
    )

def fail(
    error: ErrorCode,
    message: str = None,
    data: Any = None
) -> Response:
    """
    创建失败响应
    """
    return JSONResponse(
        status_code=error.http,
        content=jsonable_encoder({
            "code": error.business,
            "message": message or error.message,
            "data": data
        })
    )
