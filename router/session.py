import logging
import uuid
import hashlib
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import re
from urllib.parse import urlparse

from database import db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/session",
    tags=["YiPet Session Management"],
    responses={404: {"description": "未找到"}},
)

COLLECTION_NAME = "sessions"


async def ensure_db_initialized():
    """确保数据库已初始化"""
    if not hasattr(db, '_initialized') or not db._initialized:
        await db.initialize()


def normalize_session_id(session_id: str) -> str:
    """
    规范化 session_id：如果 session_id 是 URL 格式，则进行 MD5 处理
    
    Args:
        session_id: 原始 session_id
    
    Returns:
        规范化后的 session_id
    """
    if not session_id:
        return session_id
    
    # 检查是否是 URL 格式
    try:
        result = urlparse(session_id)
        # 如果包含 scheme 或 netloc，认为是 URL 格式
        if result.scheme or result.netloc:
            # 使用 MD5 处理 URL
            md5_hash = hashlib.md5(session_id.encode('utf-8')).hexdigest()
            return md5_hash
    except Exception:
        # 如果解析失败，可能不是标准 URL，直接返回原值
        pass
    
    return session_id


def get_user_id(request: Request, user_id: Optional[str] = None) -> str:
    """获取用户ID，优先级：参数 > X-User 请求头 > 默认值"""
    if user_id:
        return user_id
    
    x_user = request.headers.get("X-User", "")
    if x_user:
        return x_user
    
    return "default_user"


class SaveSessionRequest(BaseModel):
    """保存会话请求"""
    id: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    pageTitle: Optional[str] = None
    pageDescription: Optional[str] = None
    pageContent: Optional[str] = None
    messages: List[Dict[str, Any]] = []
    createdAt: Optional[int] = None
    updatedAt: Optional[int] = None
    lastAccessTime: Optional[int] = None
    user_id: Optional[str] = None


class SessionListRequest(BaseModel):
    """会话列表请求"""
    user_id: Optional[str] = None
    limit: int = 50
    skip: int = 0


class SearchSessionRequest(BaseModel):
    """搜索会话请求"""
    query: str
    user_id: Optional[str] = None
    limit: int = 10


@router.get("/status")
async def get_status():
    """检查会话服务状态"""
    try:
        await ensure_db_initialized()
        return {
            "available": True,
            "message": "会话服务可用"
        }
    except Exception as e:
        logger.error(f"检查状态失败: {str(e)}")
        return {
            "available": False,
            "message": f"会话服务不可用: {str(e)}"
        }


@router.post("/save")
async def save_session(request: SaveSessionRequest, http_request: Request):
    """保存YiPet会话数据到后端"""
    try:
        await ensure_db_initialized()
        user_id = get_user_id(http_request, request.user_id)
        
        # 生成或使用现有的会话ID
        session_id = request.id
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # 规范化 session_id：如果是 URL 格式，则进行 MD5 处理
        session_id = normalize_session_id(session_id)
        
        # 获取当前时间
        current_time = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        # 构建会话文档
        session_doc = {
            "key": session_id,
            "user_id": user_id,
            "url": request.url or "",
            "title": request.title or "",
            "pageTitle": request.pageTitle or "",
            "pageDescription": request.pageDescription or "",
            "pageContent": request.pageContent or "",
            "messages": request.messages or [],
            "createdAt": request.createdAt or current_time,
            "updatedAt": request.updatedAt or current_time,
            "lastAccessTime": request.lastAccessTime or current_time,
            "createdTime": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            "updatedTime": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 检查是否已存在
        collection = db.mongodb.db[COLLECTION_NAME]
        existing = await collection.find_one({"key": session_id})
        
        if existing:
            # 更新现有会话（保留createdAt和order，增量更新）
            # 优化：只在有变化时才更新
            update_doc = {}
            needs_update = False
            
            # 检查是否需要更新时间戳（如果消息或其他关键字段有变化）
            should_update_timestamp = False
            
            if request.messages is not None:
                existing_messages = existing.get("messages", [])
                if len(request.messages) != len(existing_messages):
                    update_doc["messages"] = request.messages or []
                    needs_update = True
                    should_update_timestamp = True
                elif request.messages != existing_messages:
                    update_doc["messages"] = request.messages or []
                    needs_update = True
                    should_update_timestamp = True
            
            if request.url is not None and request.url != existing.get("url", ""):
                update_doc["url"] = request.url or ""
                needs_update = True
            if request.title is not None and request.title != existing.get("title", ""):
                update_doc["title"] = request.title or ""
                needs_update = True
            if request.pageTitle is not None and request.pageTitle != existing.get("pageTitle", ""):
                update_doc["pageTitle"] = request.pageTitle or ""
                needs_update = True
            if request.pageDescription is not None and request.pageDescription != existing.get("pageDescription", ""):
                update_doc["pageDescription"] = request.pageDescription or ""
                needs_update = True
            if request.pageContent is not None and request.pageContent != existing.get("pageContent", ""):
                update_doc["pageContent"] = request.pageContent or ""
                needs_update = True
            
            # 更新时间戳
            if request.updatedAt is not None:
                if request.updatedAt != existing.get("updatedAt", 0):
                    update_doc["updatedAt"] = request.updatedAt
                    needs_update = True
            elif should_update_timestamp:
                update_doc["updatedAt"] = current_time
                needs_update = True
            
            if request.lastAccessTime is not None:
                if request.lastAccessTime != existing.get("lastAccessTime", 0):
                    update_doc["lastAccessTime"] = request.lastAccessTime
                    needs_update = True
            elif should_update_timestamp:
                update_doc["lastAccessTime"] = current_time
                needs_update = True
            
            if should_update_timestamp:
                update_doc["updatedTime"] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            
            # 只在有变化时才执行更新
            if needs_update:
                await collection.update_one(
                    {"key": session_id},
                    {"$set": update_doc}
                )
        else:
            # 插入新会话，设置order字段
            max_order_doc = await collection.find_one(
                sort=[("order", -1)],
                projection={"order": 1}
            )
            max_order = max_order_doc.get("order", 0) if max_order_doc else 0
            session_doc["order"] = max_order + 1
            await collection.insert_one(session_doc)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "session_id": session_id,
                "id": session_id
            },
            "message": "会话保存成功"
        })
    except Exception as e:
        logger.error(f"保存会话失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"保存会话失败: {str(e)}")


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    http_request: Request,
    user_id: Optional[str] = None
):
    """根据会话ID获取会话数据"""
    try:
        await ensure_db_initialized()
        user_id = get_user_id(http_request, user_id)
        
        # 规范化 session_id：如果是 URL 格式，则进行 MD5 处理
        session_id = normalize_session_id(session_id)
        
        collection = db.mongodb.db[COLLECTION_NAME]
        session_doc = await collection.find_one(
            {"key": session_id},
            {"_id": 0}
        )
        
        if not session_doc:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
        # 转换为API响应格式
        session_data = {
            "id": session_doc.get("key"),
            "url": session_doc.get("url", ""),
            "title": session_doc.get("title", ""),
            "pageTitle": session_doc.get("pageTitle", ""),
            "pageDescription": session_doc.get("pageDescription", ""),
            "pageContent": session_doc.get("pageContent", ""),
            "messages": session_doc.get("messages", []),
            "createdAt": session_doc.get("createdAt"),
            "updatedAt": session_doc.get("updatedAt"),
            "lastAccessTime": session_doc.get("lastAccessTime")
        }
        
        return JSONResponse(content={
            "success": True,
            "data": session_data,
            "message": "获取会话成功"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取会话失败: {str(e)}")


@router.get("/")
async def list_sessions(
    http_request: Request,
    user_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """列出所有会话"""
    try:
        await ensure_db_initialized()
        user_id = get_user_id(http_request, user_id)
        
        collection = db.mongodb.db[COLLECTION_NAME]
        
        # 构建查询条件
        query = {}
        if user_id and user_id != "default_user":
            query["user_id"] = user_id
        
        # 查询会话，按更新时间倒序
        cursor = collection.find(query, {"_id": 0}) \
            .sort([("updatedAt", -1), ("order", -1)]) \
            .skip(skip) \
            .limit(limit)
        
        session_docs = await cursor.to_list(length=limit)
        
        # 去重：按 key 分组，每个 key 只保留 updatedAt 最新的那个会话
        session_map = {}
        for doc in session_docs:
            session_key = doc.get("key")
            if not session_key:
                continue
            
            # 如果该 key 已存在，比较 updatedAt，保留更新的
            if session_key in session_map:
                existing_updated_at = session_map[session_key].get("updatedAt", 0)
                current_updated_at = doc.get("updatedAt", 0)
                if current_updated_at > existing_updated_at:
                    session_map[session_key] = doc
            else:
                session_map[session_key] = doc
        
        # 转换为API响应格式
        sessions = []
        for doc in session_map.values():
            sessions.append({
                "id": doc.get("key"),
                "url": doc.get("url", ""),
                "title": doc.get("title", ""),
                "pageTitle": doc.get("pageTitle", ""),
                "message_count": len(doc.get("messages", [])),
                "createdAt": doc.get("createdAt"),
                "updatedAt": doc.get("updatedAt"),
                "lastAccessTime": doc.get("lastAccessTime")
            })
        
        # 重新排序，确保顺序正确（按 updatedAt 倒序）
        sessions.sort(key=lambda x: (x.get("updatedAt", 0), x.get("id", "")), reverse=True)
        
        return JSONResponse(content={
            "success": True,
            "count": len(sessions),
            "sessions": sessions,
            "message": f"获取到 {len(sessions)} 个会话"
        })
    except Exception as e:
        logger.error(f"列出会话失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"列出会话失败: {str(e)}")


@router.post("/search")
async def search_sessions(request: SearchSessionRequest, http_request: Request):
    """搜索会话"""
    try:
        await ensure_db_initialized()
        user_id = get_user_id(http_request, request.user_id)
        
        collection = db.mongodb.db[COLLECTION_NAME]
        
        # 构建搜索条件
        query = {}
        if user_id and user_id != "default_user":
            query["user_id"] = user_id
        
        # 构建文本搜索条件（在title、pageTitle、pageContent中搜索）
        search_query = re.compile(f'.*{re.escape(request.query)}.*', re.IGNORECASE)
        query["$or"] = [
            {"title": search_query},
            {"pageTitle": search_query},
            {"pageContent": search_query},
            {"pageDescription": search_query}
        ]
        
        # 查询会话
        cursor = collection.find(query, {"_id": 0}) \
            .sort([("updatedAt", -1), ("order", -1)]) \
            .limit(request.limit)
        
        session_docs = await cursor.to_list(length=request.limit)
        
        # 去重：按 key 分组，每个 key 只保留 updatedAt 最新的那个会话
        session_map = {}
        for doc in session_docs:
            session_key = doc.get("key")
            if not session_key:
                continue
            
            # 如果该 key 已存在，比较 updatedAt，保留更新的
            if session_key in session_map:
                existing_updated_at = session_map[session_key].get("updatedAt", 0)
                current_updated_at = doc.get("updatedAt", 0)
                if current_updated_at > existing_updated_at:
                    session_map[session_key] = doc
            else:
                session_map[session_key] = doc
        
        # 转换为API响应格式
        sessions = []
        for doc in session_map.values():
            sessions.append({
                "id": doc.get("key"),
                "url": doc.get("url", ""),
                "title": doc.get("title", ""),
                "pageTitle": doc.get("pageTitle", ""),
                "message_count": len(doc.get("messages", [])),
                "createdAt": doc.get("createdAt"),
                "updatedAt": doc.get("updatedAt"),
                "lastAccessTime": doc.get("lastAccessTime")
            })
        
        # 重新排序，确保顺序正确（按 updatedAt 倒序）
        sessions.sort(key=lambda x: (x.get("updatedAt", 0), x.get("id", "")), reverse=True)
        
        return JSONResponse(content={
            "success": True,
            "count": len(sessions),
            "sessions": sessions,
            "message": f"找到 {len(sessions)} 个相关会话"
        })
    except Exception as e:
        logger.error(f"搜索会话失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索会话失败: {str(e)}")


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    http_request: Request,
    user_id: Optional[str] = None
):
    """删除会话"""
    try:
        await ensure_db_initialized()
        user_id = get_user_id(http_request, user_id)
        
        # 规范化 session_id：如果是 URL 格式，则进行 MD5 处理
        session_id = normalize_session_id(session_id)
        
        collection = db.mongodb.db[COLLECTION_NAME]
        
        # 构建删除条件
        query = {"key": session_id}
        if user_id and user_id != "default_user":
            query["user_id"] = user_id
        
        result = await collection.delete_one(query)
        success = result.deleted_count > 0
        
        return JSONResponse(content={
            "success": success,
            "message": "会话删除成功" if success else "会话删除失败或不存在"
        })
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


@router.put("/{session_id}")
async def update_session(
    session_id: str,
    request: SaveSessionRequest,
    http_request: Request
):
    """更新会话数据"""
    try:
        await ensure_db_initialized()
        user_id = get_user_id(http_request, request.user_id)
        
        # 规范化 session_id：如果是 URL 格式，则进行 MD5 处理
        session_id = normalize_session_id(session_id)
        
        collection = db.mongodb.db[COLLECTION_NAME]
        
        # 检查会话是否存在
        existing = await collection.find_one({"key": session_id})
        if not existing:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
        # 获取当前时间
        current_time = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        # 构建更新数据（保留原有数据，只更新提供的字段）
        update_doc = {
            "updatedTime": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if request.url is not None:
            update_doc["url"] = request.url
        if request.title is not None:
            update_doc["title"] = request.title
        if request.pageTitle is not None:
            update_doc["pageTitle"] = request.pageTitle
        if request.pageDescription is not None:
            update_doc["pageDescription"] = request.pageDescription
        if request.pageContent is not None:
            update_doc["pageContent"] = request.pageContent
        if request.messages is not None:
            update_doc["messages"] = request.messages
        if request.updatedAt is not None:
            update_doc["updatedAt"] = request.updatedAt
        else:
            update_doc["updatedAt"] = current_time
        if request.lastAccessTime is not None:
            update_doc["lastAccessTime"] = request.lastAccessTime
        else:
            update_doc["lastAccessTime"] = current_time
        
        # 更新会话
        await collection.update_one(
            {"key": session_id},
            {"$set": update_doc}
        )
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "session_id": session_id,
                "id": session_id
            },
            "message": "会话更新成功"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新会话失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新会话失败: {str(e)}")

