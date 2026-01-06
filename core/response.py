"""响应对象封装
- 定义统一的响应对象 Resp，用于在 Service 层返回标准化的结果
- 提供 RespOk 和 RespFail 辅助函数用于 API 层构建响应
"""
from typing import Union

from fastapi import status as http_status
from fastapi.responses import JSONResponse, Response
from fastapi.encoders import jsonable_encoder
from core.error_codes import (
    ErrorCode, OK,
    INVALID_REQUEST, INVALID_PARAMS, BUSINESS_ERROR,
    DATA_NOT_FOUND, DATA_STORE_FAIL, DATA_UPDATE_FAIL, DATA_DESTROY_FAIL,
    PERMISSION_DENIED, SERVER_ERROR
)

class StandardResponse(object):
    """
    标准响应对象，用于封装业务层返回的状态和数据
    
    Example:
        >>> resp = StandardResponse(100, "Success", 200)
        >>> resp.set_message("New Message")
    """
    def __init__(self, status: int, message: str, code: int):
        self.status = status    # 业务状态码
        self.message = message  # 提示消息
        self.code = code        # HTTP 状态码

    def set_message(self, message):
        """
        修改响应消息
        
        Args:
            message: 新的消息内容
            
        Returns:
            StandardResponse: 自身实例，支持链式调用
        """
        self.message = message
        return self

# 预定义常用响应对象
InvalidRequest: StandardResponse = StandardResponse(INVALID_REQUEST.business, INVALID_REQUEST.message, INVALID_REQUEST.http)
InvalidParams: StandardResponse = StandardResponse(INVALID_PARAMS.business, INVALID_PARAMS.message, INVALID_PARAMS.http)
BusinessError: StandardResponse = StandardResponse(BUSINESS_ERROR.business, BUSINESS_ERROR.message, BUSINESS_ERROR.http)
DataNotFound: StandardResponse = StandardResponse(DATA_NOT_FOUND.business, DATA_NOT_FOUND.message, DATA_NOT_FOUND.http)
DataStoreFail: StandardResponse = StandardResponse(DATA_STORE_FAIL.business, DATA_STORE_FAIL.message, DATA_STORE_FAIL.http)
DataUpdateFail: StandardResponse = StandardResponse(DATA_UPDATE_FAIL.business, DATA_UPDATE_FAIL.message, DATA_UPDATE_FAIL.http)
DataDestroyFail: StandardResponse = StandardResponse(DATA_DESTROY_FAIL.business, DATA_DESTROY_FAIL.message, DATA_DESTROY_FAIL.http)
PermissionDenied: StandardResponse = StandardResponse(PERMISSION_DENIED.business, PERMISSION_DENIED.message, PERMISSION_DENIED.http)
ServerError: StandardResponse = StandardResponse(SERVER_ERROR.business, SERVER_ERROR.message, SERVER_ERROR.http)

def success(*, data: Union[list, dict, str] = None, pagination: dict = None, message: str = "success") -> Response:
    """
    创建成功响应 (200 OK)
    兼容旧版接口调用
    
    Args:
        data: 响应数据
        pagination: 分页信息
        message: 成功消息
        
    Returns:
        Response: FastAPI 响应对象
        
    Example:
        >>> resp = success(data={"id": 1})
    """
    from core.utils import create_legacy_success_response
    return create_legacy_success_response(data=data, pagination=pagination, message=message)


def fail(response: StandardResponse) -> Response:
    """
    创建失败响应 (基于 Resp 对象)
    
    Args:
        response: StandardResponse 对象
        
    Returns:
        Response: FastAPI 响应对象
        
    Example:
        >>> resp = fail(InvalidParams)
    """
    return JSONResponse(
        status_code=resp.code,
        content=jsonable_encoder({
            'status': resp.status,  # 业务码
            'code': resp.code,      # HTTP状态码 (兼容)
            'msg': resp.msg,
            'message': resp.msg     # 兼容字段
        })
    )

