import logging, json
from fastapi import APIRouter, Query, Body, HTTPException # type: ignore
from pydantic import BaseModel
from typing import Optional, Dict, Any

from Resp import RespOk

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["base"])

# 定义POST请求的数据模型
class ExecuteRequest(BaseModel):
    module_name: str = "modules.crawler.crawler"
    method_name: str = "main"
    params: Dict[str, Any] = {"url": "https://www.qbitai.com/"}

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
    # 导入动态加载模块所需的库
    import importlib
    # 导入异步支持库
    import asyncio
    
    try:
        # 将字符串转换为字典
        params_dict = json.loads(params)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="参数格式错误，请提供有效的JSON字符串")
    
    try:
        # 动态导入指定的模块
        module = importlib.import_module(module_name)
        # 从模块中获取指定的方法
        main_func = getattr(module, method_name)
    except (ImportError, AttributeError) as e:
        raise HTTPException(status_code=422, detail=f"模块或方法不存在: {str(e)}")
    
    try:
        # 检查函数是否为协程函数
        if asyncio.iscoroutinefunction(main_func):
            # 如果是协程函数，直接await
            result = await main_func(params_dict)
        else:
            # 如果是普通函数，直接调用
            result = main_func(params_dict)
        # 返回执行结果
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行函数时发生错误: {str(e)}")

@router.post("/")
async def post_module_to_execute(request: ExecuteRequest):
    # 导入动态加载模块所需的库
    import importlib
    # 导入异步支持库
    import asyncio
    
    try:
        # 验证请求数据
        if not request.module_name or not request.method_name:
            raise HTTPException(status_code=422, detail="模块名和方法名不能为空")
        
        # 动态导入指定的模块
        module = importlib.import_module(request.module_name)
        # 从模块中获取指定的方法
        main_func = getattr(module, request.method_name)
    except (ImportError, AttributeError) as e:
        raise HTTPException(status_code=422, detail=f"模块或方法不存在: {str(e)}")
    
    try:
        # 检查函数是否为协程函数
        if asyncio.iscoroutinefunction(main_func):
            # 如果是协程函数，直接await
            result = await main_func(request.params)
        else:
            # 如果是普通函数，直接调用
            result = main_func(request.params)
        # 返回执行结果
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行函数时发生错误: {str(e)}")