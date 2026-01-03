import logging, json, os
from typing import Dict, Any, Union
from pydantic import BaseModel, Field
from fastapi import APIRouter, Query, HTTPException

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/module", tags=["base"])

# 允许执行的模块/方法白名单（逗号分隔，格式: "module.path:method"）
# 出于安全考虑，默认只允许 crawler 的 main
_allowlist_env = os.getenv("MODULE_EXEC_ALLOWLIST", "modules.crawler.crawler:main")
MODULE_EXEC_ALLOWLIST = {item.strip() for item in _allowlist_env.split(",") if item.strip()}

def _parse_params(params: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """将 params 解析为 dict（支持 JSON 字符串或 dict）。"""
    if isinstance(params, dict):
        return params
    if not isinstance(params, str):
        raise HTTPException(status_code=400, detail="params 必须是 JSON 字符串或对象")
    try:
        parsed = json.loads(params)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {str(e)}")
        raise HTTPException(status_code=400, detail=f"参数格式错误，请提供有效的JSON字符串: {str(e)}")
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="params JSON 解析结果必须是对象")
    return parsed

async def _execute_module(module_name: str, method_name: str, params: Union[Dict[str, Any], str]) -> Any:
    """动态执行模块方法（受 allowlist 限制）。"""
    import importlib
    import asyncio

    if not module_name or not method_name:
        raise HTTPException(status_code=400, detail="模块名和方法名不能为空")

    allow_key = f"{module_name}:{method_name}"
    if allow_key not in MODULE_EXEC_ALLOWLIST:
        raise HTTPException(status_code=403, detail=f"禁止执行: {allow_key}")

    params_dict = _parse_params(params)

    try:
        module = importlib.import_module(module_name)
        main_func = getattr(module, method_name)
    except (ImportError, AttributeError) as e:
        logger.error(f"模块导入错误: {str(e)}")
        raise HTTPException(status_code=422, detail=f"模块或方法不存在: {str(e)}")

    try:
        if asyncio.iscoroutinefunction(main_func):
            return await main_func(params_dict)
        return main_func(params_dict)
    except Exception as e:
        logger.error(f"函数执行错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"执行函数时发生错误: {str(e)}")

# 定义POST请求的数据模型
class ExecuteRequest(BaseModel):
    module_name: str = "modules.crawler.crawler"
    method_name: str = "main"
    params: Union[Dict[str, Any], str] = Field(default_factory=lambda: {"url": "https://www.qbitai.com/"})

    class Config:
        # 允许任意类型的字段值
        arbitrary_types_allowed = True

# 同时支持GET和POST两种HTTP请求方法的路由
@router.get("/")
async def read_module_to_execute(
    # 设置默认模块名为modules.crawler
    module_name: str = "modules.crawler.crawler",
    # 设置默认方法名为main
    method_name: str = "main",
    # 使用Query参数处理params，默认值为爬取启智AI网站且最小标题长度为24
    params: str = Query(default='{"url": "https://www.qbitai.com/"}')
):
    return await _execute_module(module_name, method_name, params)

@router.post("/")
async def post_module_to_execute(request: ExecuteRequest):
    # 记录请求信息用于调试
    logger.info(f"执行模块: {request.module_name}, 方法: {request.method_name}")
    logger.info(f"参数: {request.params}")
    return await _execute_module(request.module_name, request.method_name, request.params)
