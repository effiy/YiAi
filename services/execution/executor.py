"""受控模块执行器
- 校验白名单，解析参数，按同步/异步调用目标函数
"""
import importlib
import asyncio
import logging
import json
from typing import Dict, Any, Union
from fastapi import HTTPException
from core.config import settings

logger = logging.getLogger(__name__)

EXEC_ALLOWLIST = set(settings.module_allowlist)

def parse_parameters(parameters: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """
    解析参数，支持字典或 JSON 字符串
    
    Args:
        parameters: 参数字典或 JSON 字符串
        
    Returns:
        Dict[str, Any]: 解析后的参数字典
        
    Raises:
        HTTPException: 如果 JSON 格式无效或解析后不是字典
    """
    if isinstance(parameters, dict):
        return parameters
    try:
        parsed = json.loads(parameters)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="Parameters must be a JSON object")
    return parsed

async def execute_module(module_path: str, function_name: str, parameters: Union[Dict[str, Any], str]) -> Any:
    """执行目标模块/函数
    - 验证执行白名单
    - 支持 dict 或 JSON 字符串参数
    - 自动区分异步/同步函数

    Example:
        GET /?module_name=services.execution.executor&method_name=execute_module&parameters={"module_path": "services.web.crawler.crawler_service", "function_name": "crawl_and_extract", "parameters": {"url": "https://example.com"}}
    """
    if not module_path or not function_name:
        raise HTTPException(status_code=400, detail="Module path and function name required")

    allow_key = f"{module_path}:{function_name}"
    if "*" not in EXEC_ALLOWLIST and allow_key not in EXEC_ALLOWLIST:
        raise HTTPException(status_code=403, detail=f"Execution forbidden: {allow_key}")

    parameters_dict = parse_parameters(parameters)

    try:
        module = importlib.import_module(module_path)
        target_function = getattr(module, function_name)
    except (ImportError, AttributeError) as e:
        logger.error(f"Module import error: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Module or function not found: {str(e)}")

    try:
        if asyncio.iscoroutinefunction(target_function):
            return await target_function(parameters_dict)
        return target_function(parameters_dict)
    except Exception as e:
        logger.error(f"Execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

