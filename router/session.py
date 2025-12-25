"""会话管理路由 - 处理YiPet会话相关的HTTP请求"""
import logging
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request, Query
from datetime import datetime

from router.decorators import get_session_service, handle_route_errors, extract_user_id
from router.utils import get_user_id
from router.response import success_response, error_response, list_response
from constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MIN_PAGE_SIZE

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/session",
    tags=["YiPet Session Management"],
    responses={404: {"description": "未找到"}},
)

class SaveSessionRequest(BaseModel):
    """保存会话请求"""
    id: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    pageTitle: Optional[str] = None
    pageDescription: Optional[str] = None
    pageContent: Optional[str] = None
    messages: list = []
    tags: list = []
    isFavorite: Optional[bool] = False
    createdAt: Optional[int] = None
    updatedAt: Optional[int] = None
    lastAccessTime: Optional[int] = None
    user_id: Optional[str] = None
    imageDataUrl: Optional[str] = None


class SearchSessionRequest(BaseModel):
    """搜索会话请求"""
    query: str
    user_id: Optional[str] = None
    limit: int = 10


@router.get("/status")
@handle_route_errors("检查会话服务状态")
async def get_status():
    """检查会话服务状态"""
    service = await get_session_service()
    return {
        "available": True,
        "message": "会话服务可用"
    }


@router.post("/save")
@handle_route_errors("保存会话")
async def save_session(request: SaveSessionRequest, http_request: Request):
    """
    保存YiPet会话数据到后端
    
    自动判断创建或更新：
    - 如果提供了 id 且会话存在，则更新
    - 否则创建新会话
    
    返回完整的会话数据，便于前端更新缓存
    """
    service = await get_session_service()
    user_id = get_user_id(http_request, request.user_id)
    
    # 构建会话数据
    session_data = {
        "id": request.id,
        "url": request.url,
        "title": request.title,
        "pageTitle": request.pageTitle,
        "pageDescription": request.pageDescription,
        "pageContent": request.pageContent,
        "messages": request.messages,
        "tags": request.tags,
        "isFavorite": request.isFavorite if request.isFavorite is not None else False,
        "createdAt": request.createdAt,
        "updatedAt": request.updatedAt,
        "lastAccessTime": request.lastAccessTime
    }
    
    # 如果提供了 imageDataUrl，添加到会话数据中
    if request.imageDataUrl:
        session_data["imageDataUrl"] = request.imageDataUrl
    
    # 调用服务层保存会话
    result = await service.save_session(session_data, user_id=user_id)
    session_id = result["session_id"]
    is_new = result.get("is_new", False)
    
    # 获取保存后的完整会话数据，用于返回给前端
    saved_session = await service.get_session(session_id, user_id=user_id)
    
    return success_response(
        data={
            "session_id": session_id,
            "id": session_id,
            "is_new": is_new,
            "session": saved_session  # 返回完整会话数据，便于前端更新
        },
        message="会话创建成功" if is_new else "会话更新成功"
    )


@router.put("/{session_id}/favorite")
@handle_route_errors("更新收藏状态")
async def update_favorite(
    session_id: str,
    isFavorite: bool = Query(..., description="收藏状态"),
    http_request: Request = None,
    user_id: Optional[str] = None
):
    """
    更新会话的收藏状态
    
    Args:
        session_id: 会话ID
        isFavorite: 收藏状态（true/false）
        user_id: 用户ID（可选）
    
    Returns:
        更新结果
    """
    service = await get_session_service()
    user_id = get_user_id(http_request, user_id)
    
    # 更新收藏状态
    success = await service.update_session_field(session_id, "isFavorite", isFavorite, user_id=user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 获取更新后的完整会话数据
    updated_session = await service.get_session(session_id, user_id=user_id)
    
    return success_response(
        data={
            "session_id": session_id,
            "isFavorite": isFavorite,
            "session": updated_session
        },
        message="收藏状态更新成功"
    )


@router.get("/{session_id}")
@handle_route_errors("获取会话")
async def get_session(
    session_id: str,
    http_request: Request,
    user_id: Optional[str] = None
):
    """根据会话ID获取会话数据"""
    service = await get_session_service()
    user_id = get_user_id(http_request, user_id)
    
    # 调用服务层获取会话
    session_data = await service.get_session(session_id, user_id=user_id)
    
    if not session_data:
        raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
    
    return success_response(data=session_data, message="获取会话成功")


@router.get("/")
@handle_route_errors("列出会话")
async def list_sessions(
    http_request: Request,
    user_id: Optional[str] = None,
    # 默认分页：避免一次性拉取超大列表造成流量浪费
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),
    skip: int = Query(0, ge=0)
):
    """列出所有会话（默认返回所有数据）"""
    service = await get_session_service()
    user_id = get_user_id(http_request, user_id)
    
    # 调用服务层列出会话
    sessions = await service.list_sessions(user_id=user_id, limit=limit, skip=skip)
    
    return list_response(sessions)


@router.post("/search")
@handle_route_errors("搜索会话")
async def search_sessions(request: SearchSessionRequest, http_request: Request):
    """搜索会话"""
    service = await get_session_service()
    user_id = get_user_id(http_request, request.user_id)
    
    # 调用服务层搜索会话
    sessions = await service.search_sessions(
        query=request.query,
        user_id=user_id,
        limit=request.limit
    )
    
    return list_response(sessions, message=f"找到 {len(sessions)} 个相关会话")


@router.delete("/{session_id}")
@handle_route_errors("删除会话")
async def delete_session(
    session_id: str,
    http_request: Request,
    user_id: Optional[str] = None
):
    """删除会话"""
    service = await get_session_service()
    user_id = get_user_id(http_request, user_id)
    
    # 调用服务层删除会话
    success = await service.delete_session(session_id, user_id=user_id)
    
    return success_response(
        message="会话删除成功" if success else "会话删除失败或不存在"
    )


class BatchDeleteRequest(BaseModel):
    """批量删除会话请求"""
    session_ids: list
    user_id: Optional[str] = None


@router.post("/batch/delete")
@handle_route_errors("批量删除会话")
async def batch_delete_sessions(
    request: BatchDeleteRequest,
    http_request: Request
):
    """批量删除会话"""
    service = await get_session_service()
    user_id = get_user_id(http_request, request.user_id)
    
    if not request.session_ids or len(request.session_ids) == 0:
        raise HTTPException(status_code=400, detail="会话ID列表不能为空")
    
    # 调用服务层批量删除会话
    result = await service.delete_sessions(request.session_ids, user_id=user_id)
    
    return success_response(
        data=result,
        message=f"成功删除 {result['success_count']} 个会话，失败 {result['failed_count']} 个"
    )


@router.put("/{session_id}")
@handle_route_errors("更新会话")
async def update_session(
    session_id: str,
    request: SaveSessionRequest,
    http_request: Request
):
    """
    更新会话数据
    """
    service = await get_session_service()
    user_id = get_user_id(http_request, request.user_id)
    
    # 构建会话数据
    session_data = {
        "url": request.url,
        "title": request.title,
        "pageTitle": request.pageTitle,
        "pageDescription": request.pageDescription,
        "pageContent": request.pageContent,
        "messages": request.messages,
        "tags": request.tags,
        "isFavorite": request.isFavorite if request.isFavorite is not None else False,
        "updatedAt": request.updatedAt,
        "lastAccessTime": request.lastAccessTime
    }
    
    # 如果提供了 imageDataUrl，添加到会话数据中
    if request.imageDataUrl:
        session_data["imageDataUrl"] = request.imageDataUrl
    
    # 调用服务层更新会话
    result = await service.update_session(session_id, session_data, user_id=user_id)
    
    return success_response(
        data={
            "session_id": result["session_id"],
            "id": result["id"]
        },
        message="会话更新成功"
    )




