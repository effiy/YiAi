import logging
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import inspect
import json
import types
from typing import Any, AsyncIterator, Iterator, Optional, Union
from models.schemas import ExecuteRequest
from core.response import success
from services.execution.executor import execute_module

logger = logging.getLogger(__name__)
router = APIRouter()

def _format_sse(data: Any) -> bytes:
    payload: Any
    if isinstance(data, (bytes, bytearray)):
        try:
            data = data.decode("utf-8")
        except Exception:
            data = str(data)
    if isinstance(data, str):
        payload = {"data": {"message": data}}
    else:
        payload = data
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")

async def _stream_async(gen: AsyncIterator[Any]):
    try:
        async for item in gen:
            yield _format_sse(item)
    finally:
        yield _format_sse({"done": True})

def _stream_sync(gen: Iterator[Any]):
    try:
        for item in gen:
            yield _format_sse(item)
    finally:
        yield _format_sse({"done": True})

@router.get("/", operation_id="execute_module_get")
async def execute_module_via_get(
    module_name: str = "",
    method_name: str = "",
    parameters: str = Query(default='{}')
):
    """
    GET 方式执行指定模块方法
    """
    result = await execute_module(module_name, method_name, parameters)
    if inspect.isasyncgen(result) or hasattr(result, "__aiter__"):
        return StreamingResponse(
            _stream_async(result),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    if isinstance(result, types.GeneratorType):
        return StreamingResponse(
            _stream_sync(result),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    return success(data=result)

@router.post("/", operation_id="execute_module_post")
async def execute_module_via_post(request: ExecuteRequest):
    """
    POST 方式执行指定模块方法
    """
    logger.info(f"执行模块: {request.module_name}, 方法: {request.method_name}")
    logger.info(f"参数: {request.parameters}")
    result = await execute_module(request.module_name, request.method_name, request.parameters)
    if inspect.isasyncgen(result) or hasattr(result, "__aiter__"):
        return StreamingResponse(
            _stream_async(result),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    if isinstance(result, types.GeneratorType):
        return StreamingResponse(
            _stream_sync(result),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    return success(data=result)
