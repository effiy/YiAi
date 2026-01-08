import logging
from fastapi import APIRouter, Query
from core.schemas import ExecuteRequest
from core.response import success
from services.execution.executor import execute_module

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def execute_module_via_get(
    module_name: str = "services.web.crawler.crawler_service",
    method_name: str = "crawl_and_extract",
    parameters: str = Query(default='{"url": "https://www.qbitai.com/"}')
):
    """
    GET 方式执行指定模块方法
    """
    result = await execute_module(module_name, method_name, parameters)
    return success(data=result)

@router.post("/")
async def execute_module_via_post(request: ExecuteRequest):
    """
    POST 方式执行指定模块方法
    """
    logger.info(f"执行模块: {request.module_name}, 方法: {request.method_name}")
    logger.info(f"参数: {request.parameters}")
    result = await execute_module(request.module_name, request.method_name, request.parameters)
    return success(data=result)
