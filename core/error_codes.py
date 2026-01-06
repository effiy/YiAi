"""错误码定义
- 业务错误码采用 4 位分组：1xxx 为客户端错误，5xxx 为服务端错误
- 每个错误码包含 business（业务码）、http（HTTP 状态）、message（人类可读信息）
"""
from dataclasses import dataclass
from fastapi import status as http_status

@dataclass(frozen=True)
class ErrorCode:
    business: int
    http: int
    message: str

# Success
OK = ErrorCode(business=0, http=http_status.HTTP_200_OK, message="成功")

# Client errors
INVALID_REQUEST = ErrorCode(1000, http_status.HTTP_400_BAD_REQUEST, "无效的请求")
INVALID_PARAMS = ErrorCode(1002, http_status.HTTP_400_BAD_REQUEST, "无效的参数")
BUSINESS_ERROR = ErrorCode(1003, http_status.HTTP_400_BAD_REQUEST, "业务错误")
DATA_NOT_FOUND = ErrorCode(1004, http_status.HTTP_404_NOT_FOUND, "未找到资源")
UNAUTHORIZED = ErrorCode(1009, http_status.HTTP_401_UNAUTHORIZED, "未认证")
PERMISSION_DENIED = ErrorCode(1008, http_status.HTTP_403_FORBIDDEN, "权限拒绝")

# Server errors
DATA_STORE_FAIL = ErrorCode(1005, http_status.HTTP_500_INTERNAL_SERVER_ERROR, "新增失败")
DATA_UPDATE_FAIL = ErrorCode(1006, http_status.HTTP_500_INTERNAL_SERVER_ERROR, "更新失败")
DATA_DESTROY_FAIL = ErrorCode(1007, http_status.HTTP_500_INTERNAL_SERVER_ERROR, "删除失败")
SERVER_ERROR = ErrorCode(5000, http_status.HTTP_500_INTERNAL_SERVER_ERROR, "服务器繁忙")

def map_http_to_error_code(status: int) -> ErrorCode:
    if status == http_status.HTTP_401_UNAUTHORIZED:
        return UNAUTHORIZED
    if status == http_status.HTTP_404_NOT_FOUND:
        return DATA_NOT_FOUND
    if status == http_status.HTTP_403_FORBIDDEN:
        return PERMISSION_DENIED
    if status == http_status.HTTP_400_BAD_REQUEST:
        return INVALID_REQUEST
    if status == http_status.HTTP_500_INTERNAL_SERVER_ERROR:
        return SERVER_ERROR
    return SERVER_ERROR

