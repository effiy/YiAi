"""受控模块执行器
- 校验白名单，解析参数，按同步/异步调用目标函数
"""
import importlib
import asyncio
import logging
import json
import inspect
import subprocess
from typing import Dict, Any, Union
from fastapi import HTTPException
from core.settings import settings

logger = logging.getLogger(__name__)

allowlist = settings.module_allowlist
if isinstance(allowlist, str):
    allowlist = [x.strip() for x in allowlist.split(',') if x.strip()]
EXEC_ALLOWLIST = set(allowlist)

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

async def run_script(script_path: str, timeout: int = 300) -> Dict[str, Any]:
    """
    执行 Python 脚本

    Args:
        script_path: 脚本路径
        timeout: 超时时间（秒）

    Returns:
        执行结果
    """
    try:
        logger.info(f"开始执行脚本: {script_path}")

        # 使用 asyncio.create_subprocess_exec 执行脚本
        process = await asyncio.create_subprocess_exec(
            'python3',
            script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # 等待执行完成，设置超时
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise Exception(f"脚本执行超时（{timeout}秒）")

        # 解码输出
        stdout_text = stdout.decode('utf-8') if stdout else ''
        stderr_text = stderr.decode('utf-8') if stderr else ''

        logger.info(f"脚本执行完成，返回码: {process.returncode}")

        if process.returncode != 0:
            logger.error(f"脚本执行失败: {stderr_text}")
            return {
                'success': False,
                'message': f'脚本执行失败（返回码: {process.returncode}）',
                'stdout': stdout_text,
                'stderr': stderr_text,
                'returncode': process.returncode
            }

        return {
            'success': True,
            'message': '脚本执行成功',
            'stdout': stdout_text,
            'stderr': stderr_text,
            'returncode': process.returncode
        }

    except Exception as e:
        logger.error(f"执行脚本失败: {str(e)}", exc_info=True)
        return {
            'success': False,
            'message': f'执行脚本失败: {str(e)}',
            'error': str(e)
        }

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
        if inspect.isasyncgenfunction(target_function):
            return target_function(parameters_dict)
        if inspect.isgeneratorfunction(target_function):
            return target_function(parameters_dict)
        if asyncio.iscoroutinefunction(target_function):
            return await target_function(parameters_dict)
        return target_function(parameters_dict)
    except Exception as e:
        logger.error(f"Execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

