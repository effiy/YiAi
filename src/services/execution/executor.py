"""受控模块执行器
- 校验白名单，解析参数，按同步/异步调用目标函数
- 集成 Observer 沙箱和重入守卫
"""
import importlib
import asyncio
import logging
import json
import inspect
import subprocess
import time
from typing import Dict, Any, Union
from core.config import settings
from core.error_codes import ErrorCode
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)

allowlist = settings.module_allowlist
if isinstance(allowlist, str):
    allowlist = [x.strip() for x in allowlist.split(',') if x.strip()]
EXEC_ALLOWLIST = set(allowlist)

# Lazy import to avoid circular dependency at module load time
_recorder = None
_guard = None

def _get_recorder():
    global _recorder
    if _recorder is None and settings.state_store_enabled:
        try:
            from services.state.skill_recorder import get_recorder
            _recorder = get_recorder()
        except Exception as e:
            logger.warning(f"SkillRecorder not available: {e}")
    return _recorder


def _get_guard():
    global _guard
    if _guard is None and settings.observer_guard_enabled:
        try:
            from core.observer import ReentrancyGuard
            _guard = ReentrancyGuard(max_depth=settings.observer_guard_max_depth)
        except Exception as e:
            logger.warning(f"ReentrancyGuard not available: {e}")
    return _guard

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
        raise BusinessException(ErrorCode.INVALID_PARAMS, message=f"Invalid JSON: {str(e)}")
    if not isinstance(parsed, dict):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="Parameters must be a JSON object")
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

async def _run_function(target_function, parameters_dict):
    """在 Observer 沙箱上下文中执行目标函数"""
    if settings.observer_sandbox_enabled:
        from core.observer import sandbox_context
        with sandbox_context(
            fs_allowlist=settings.get_sandbox_fs_allowlist(),
            network_allowlist=settings.get_sandbox_network_allowlist(),
        ):
            if asyncio.iscoroutinefunction(target_function):
                return await target_function(parameters_dict)
            return target_function(parameters_dict)
    else:
        if asyncio.iscoroutinefunction(target_function):
            return await target_function(parameters_dict)
        return target_function(parameters_dict)


async def execute_module(module_path: str, function_name: str, parameters: Union[Dict[str, Any], str]) -> Any:
    """执行目标模块/函数
    - 验证执行白名单
    - 支持 dict 或 JSON 字符串参数
    - 自动区分异步/同步函数
    - 可选：异步记录执行结果到 State Store
    - 集成 Observer 沙箱和重入守卫

    Example:
        GET /?module_name=module.path&method_name=function_name&parameters={"key": "value"}
    """
    # Reentrancy Guard
    guard = _get_guard()
    token = None
    if guard is not None:
        from core.observer.guard import _reentrancy_depth
        depth = _reentrancy_depth.get()
        if depth >= guard.max_depth:
            raise BusinessException(
                ErrorCode.SERVER_ERROR,
                message=f"Reentrancy depth {depth} exceeds limit {guard.max_depth}"
            )
        token = _reentrancy_depth.set(depth + 1)

    try:
        if not module_path or not function_name:
            raise BusinessException(ErrorCode.INVALID_PARAMS, message="Module path and function name required")

        allow_key = f"{module_path}:{function_name}"
        if "*" not in EXEC_ALLOWLIST and allow_key not in EXEC_ALLOWLIST:
            raise BusinessException(ErrorCode.PERMISSION_DENIED, message=f"Execution forbidden: {allow_key}")

        parameters_dict = parse_parameters(parameters)

        try:
            module = importlib.import_module(module_path)
            target_function = getattr(module, function_name)
        except (ImportError, AttributeError) as e:
            logger.error(f"Module import error: {str(e)}")
            raise BusinessException(ErrorCode.INVALID_PARAMS, message=f"Module or function not found: {str(e)}")

        start = time.perf_counter()
        status = "success"
        error_message = ""
        result = None

        try:
            if inspect.isasyncgenfunction(target_function):
                result = target_function(parameters_dict)
            elif inspect.isgeneratorfunction(target_function):
                result = target_function(parameters_dict)
            elif asyncio.iscoroutinefunction(target_function):
                result = await _run_function(target_function, parameters_dict)
            else:
                result = await _run_function(target_function, parameters_dict)
        except Exception as e:
            status = "failed"
            error_message = str(e)
            logger.error(f"Execution error: {str(e)}")
            raise BusinessException(ErrorCode.INTERNAL_ERROR, message=f"Execution failed: {str(e)}") from e
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            recorder = _get_recorder()
            if recorder is not None:
                try:
                    recorder.record_async(
                        skill_name=f"{module_path}:{function_name}",
                        status=status,
                        duration_ms=duration_ms,
                        input_summary=str(parameters)[:500],
                        output_summary=str(result)[:500] if result else "",
                        error_message=error_message,
                    )
                except Exception as rec_err:
                    logger.error(f"SkillRecorder failed: {rec_err}")

        return result
    finally:
        if token is not None:
            from core.observer.guard import _reentrancy_depth
            _reentrancy_depth.reset(token)

