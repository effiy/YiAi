"""错误码定义
- 业务错误码采用 4 位分组：1xxx 为客户端错误，5xxx 为服务端错误
- 使用枚举管理所有错误码
"""
from enum import Enum
from dataclasses import dataclass
from fastapi import status as http_status

@dataclass(frozen=True)
class ErrorInfo:
    business: int
    http: int
    message: str

class ErrorCode(Enum):
    # Success
    OK = ErrorInfo(0, http_status.HTTP_200_OK, "成功")

    # Client errors
    INVALID_REQUEST = ErrorInfo(1000, http_status.HTTP_400_BAD_REQUEST, "无效的请求")
    INVALID_PARAMS = ErrorInfo(1002, http_status.HTTP_400_BAD_REQUEST, "无效的参数")
    BUSINESS_ERROR = ErrorInfo(1003, http_status.HTTP_400_BAD_REQUEST, "业务错误")
    DATA_NOT_FOUND = ErrorInfo(1004, http_status.HTTP_404_NOT_FOUND, "未找到资源")
    UNAUTHORIZED = ErrorInfo(1009, http_status.HTTP_401_UNAUTHORIZED, "未认证")
    PERMISSION_DENIED = ErrorInfo(1008, http_status.HTTP_403_FORBIDDEN, "权限拒绝")

    # Server errors
    DATA_STORE_FAIL = ErrorInfo(1005, http_status.HTTP_500_INTERNAL_SERVER_ERROR, "新增失败")
    DATA_UPDATE_FAIL = ErrorInfo(1006, http_status.HTTP_500_INTERNAL_SERVER_ERROR, "更新失败")
    DATA_DESTROY_FAIL = ErrorInfo(1007, http_status.HTTP_500_INTERNAL_SERVER_ERROR, "删除失败")
    SERVER_ERROR = ErrorInfo(5000, http_status.HTTP_500_INTERNAL_SERVER_ERROR, "服务器繁忙")

    @property
    def business(self) -> int:
        return self.value.business

    @property
    def http(self) -> int:
        return self.value.http

    @property
    def message(self) -> str:
        return self.value.message

def map_http_to_error_code(status: int) -> ErrorCode:
    """根据 HTTP 状态码映射到业务错误码"""
    mapping = {
        http_status.HTTP_401_UNAUTHORIZED: ErrorCode.UNAUTHORIZED,
        http_status.HTTP_404_NOT_FOUND: ErrorCode.DATA_NOT_FOUND,
        http_status.HTTP_403_FORBIDDEN: ErrorCode.PERMISSION_DENIED,
        http_status.HTTP_400_BAD_REQUEST: ErrorCode.INVALID_REQUEST,
        http_status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorCode.SERVER_ERROR,
    }
    return mapping.get(status, ErrorCode.SERVER_ERROR)
