"""请求接口管理路由 - 处理YiPet请求接口相关的HTTP请求"""
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from datetime import datetime

from database import db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api-request",
    tags=["YiPet API Request Management"],
    responses={404: {"description": "未找到"}},
)


def get_user_id(request: Request, user_id: Optional[str] = None) -> str:
    """获取用户ID，优先级：参数 > X-User 请求头 > 默认值"""
    if user_id:
        return user_id
    
    x_user = request.headers.get("X-User", "")
    if x_user:
        return x_user
    
    return "default_user"


def api_request_to_list_item(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    将数据库文档转换为列表项格式（用于列表展示，不包含完整详情）
    
    Args:
        doc: MongoDB文档
        
    Returns:
        列表项格式的请求接口数据
    """
    return {
        "id": str(doc.get("_id", "")),
        "key": doc.get("key", ""),
        "url": doc.get("url", ""),
        "method": doc.get("method", "GET"),
        "status": doc.get("status", 0),
        "statusText": doc.get("statusText", ""),
        "duration": doc.get("duration", 0),
        "timestamp": doc.get("timestamp") or doc.get("createdAt") or doc.get("updatedAt"),
        "tags": doc.get("tags", []),
        "pageUrl": doc.get("pageUrl", ""),
        # 列表项不包含完整详情，减少数据传输
        "headers": {},
        "body": None,
        "responseHeaders": {},
        "responseText": "",
        "responseBody": None,
        "curl": "",
    }


@router.get("/")
async def list_api_requests(
    http_request: Request,
    user_id: Optional[str] = None,
    limit: int = Query(10000, ge=1),
    skip: int = Query(0, ge=0)
):
    """列出所有请求接口（返回简化版列表，不包含完整详情）"""
    try:
        await db.initialize()
        user_id = get_user_id(http_request, user_id)
        
        # 构建查询条件
        query = {}
        if user_id and user_id != "default_user":
            query["user_id"] = user_id
        
        # 查询请求接口，按时间戳倒序
        collection = db.get_collection("apis")
        cursor = collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        
        # 转换为列表项格式
        api_requests = []
        for doc in docs:
            api_requests.append(api_request_to_list_item(doc))
        
        return JSONResponse(content={
            "success": True,
            "count": len(api_requests),
            "apiRequests": api_requests,
            "message": f"获取到 {len(api_requests)} 个请求接口"
        })
    except Exception as e:
        logger.error(f"列出请求接口失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"列出请求接口失败: {str(e)}")


@router.get("/{request_id}")
async def get_api_request(
    request_id: str,
    http_request: Request,
    user_id: Optional[str] = None
):
    """根据请求ID获取请求接口详情（包含完整信息）"""
    try:
        await db.initialize()
        user_id = get_user_id(http_request, user_id)
        
        # 构建查询条件
        query = {}
        if user_id and user_id != "default_user":
            query["user_id"] = user_id
        
        # 尝试通过_id或key查找
        from bson import ObjectId
        try:
            query["_id"] = ObjectId(request_id)
        except:
            query["key"] = request_id
        
        collection = db.get_collection("apis")
        doc = await collection.find_one(query)
        
        if not doc:
            raise HTTPException(status_code=404, detail=f"请求接口 {request_id} 不存在")
        
        # 返回完整数据
        api_request = {
            "id": str(doc.get("_id", "")),
            "key": doc.get("key", ""),
            "url": doc.get("url", ""),
            "method": doc.get("method", "GET"),
            "status": doc.get("status", 0),
            "statusText": doc.get("statusText", ""),
            "duration": doc.get("duration", 0),
            "timestamp": doc.get("timestamp") or doc.get("createdAt") or doc.get("updatedAt"),
            "tags": doc.get("tags", []),
            "pageUrl": doc.get("pageUrl", ""),
            "headers": doc.get("headers", {}),
            "body": doc.get("body"),
            "responseHeaders": doc.get("responseHeaders", {}),
            "responseText": doc.get("responseText", ""),
            "responseBody": doc.get("responseBody"),
            "curl": doc.get("curl", ""),
            "type": doc.get("type", "api"),
            "source": doc.get("source", "api"),
        }
        
        return JSONResponse(content={
            "success": True,
            "data": api_request,
            "message": "获取请求接口详情成功"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取请求接口详情失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取请求接口详情失败: {str(e)}")


