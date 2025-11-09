"""会话管理路由 - 处理YiPet会话相关的HTTP请求"""
import logging
import base64
import os
import oss2
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from datetime import datetime

from modules.services.sessionService import SessionService
from router.oss import get_oss_config, build_oss_url

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/session",
    tags=["YiPet Session Management"],
    responses={404: {"description": "未找到"}},
)

# 创建服务实例（单例模式）
_session_service: Optional[SessionService] = None


async def get_session_service() -> SessionService:
    """获取会话服务实例（懒加载）"""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
        await _session_service.initialize()
    return _session_service


def get_user_id(request: Request, user_id: Optional[str] = None) -> str:
    """获取用户ID，优先级：参数 > X-User 请求头 > 默认值"""
    if user_id:
        return user_id
    
    x_user = request.headers.get("X-User", "")
    if x_user:
        return x_user
    
    return "default_user"


async def upload_base64_image_to_oss(image_data_url: str, directory: str = "session_images") -> Optional[str]:
    """
    将 base64 格式的图片上传到 OSS
    
    Args:
        image_data_url: data:image/png;base64,xxx 格式的图片数据
        directory: OSS 存储目录，默认为 session_images
    
    Returns:
        上传成功返回 OSS URL，失败返回 None
    """
    try:
        # 检查是否是 base64 格式的 data URL
        if not image_data_url or not image_data_url.startswith("data:image/"):
            return None
        
        # 提取 MIME 类型和 base64 数据
        if ";" in image_data_url and "," in image_data_url:
            # 格式: data:image/png;base64,xxxxx
            header, data = image_data_url.split(",", 1)
            mime_type = header.split(":")[1].split(";")[0]  # image/png
        else:
            logger.warning(f"无效的 data URL 格式: {image_data_url[:50]}...")
            return None
        
        # 确定文件扩展名
        ext_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/gif": ".gif",
            "image/webp": ".webp"
        }
        file_ext = ext_map.get(mime_type, ".png")
        
        # 解码 base64 数据
        try:
            image_data = base64.b64decode(data)
        except Exception as e:
            logger.error(f"Base64 解码失败: {str(e)}")
            return None
        
        # 检查文件大小（默认限制 50MB）
        max_size = int(os.getenv("OSS_MAX_FILE_SIZE", "50")) * 1024 * 1024
        if len(image_data) > max_size:
            logger.error(f"图片大小超过限制: {len(image_data)} 字节")
            return None
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        object_name = f"{directory}/{timestamp}{file_ext}"
        
        # 获取 OSS 配置并创建 bucket
        config = get_oss_config()
        auth = oss2.Auth(config.access_key_id, config.access_key_secret)
        bucket = oss2.Bucket(auth, config.endpoint, config.bucket_name)
        
        # 上传到 OSS
        bucket.put_object(object_name, image_data)
        file_url = build_oss_url(config.bucket_name, config.endpoint, object_name)
        
        logger.info(f"Base64 图片上传成功: {object_name} (大小: {len(image_data)} 字节)")
        return file_url
        
    except Exception as e:
        logger.error(f"上传 base64 图片到 OSS 失败: {str(e)}", exc_info=True)
        return None


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
async def get_status():
    """检查会话服务状态"""
    try:
        service = await get_session_service()
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
    """
    保存YiPet会话数据到后端
    
    自动判断创建或更新：
    - 如果提供了 id 且会话存在，则更新
    - 否则创建新会话
    
    如果提供了 imageDataUrl 且为 base64 格式，会自动上传到 OSS 并替换为 URL
    
    返回完整的会话数据，便于前端更新缓存
    """
    try:
        service = await get_session_service()
        user_id = get_user_id(http_request, request.user_id)
        
        # 处理 imageDataUrl：如果是 base64 格式，上传到 OSS 并替换为 URL
        image_url = request.imageDataUrl
        if image_url and image_url.startswith("data:image/"):
            oss_url = await upload_base64_image_to_oss(image_url)
            if oss_url:
                image_url = oss_url
                logger.info(f"图片已上传到 OSS: {oss_url}")
            else:
                logger.warning(f"图片上传到 OSS 失败，保留原始 data URL")
        
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
            "createdAt": request.createdAt,
            "updatedAt": request.updatedAt,
            "lastAccessTime": request.lastAccessTime
        }
        
        # 如果 imageDataUrl 已处理，添加到会话数据中
        if image_url:
            session_data["imageDataUrl"] = image_url
        
        # 调用服务层保存会话
        result = await service.save_session(session_data, user_id=user_id)
        session_id = result["session_id"]
        is_new = result.get("is_new", False)
        
        # 获取保存后的完整会话数据，用于返回给前端
        saved_session = await service.get_session(session_id, user_id=user_id)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "session_id": session_id,
                "id": session_id,
                "is_new": is_new,
                "session": saved_session  # 返回完整会话数据，便于前端更新
            },
            "message": "会话创建成功" if is_new else "会话更新成功"
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
        service = await get_session_service()
        user_id = get_user_id(http_request, user_id)
        
        # 调用服务层获取会话
        session_data = await service.get_session(session_id, user_id=user_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
        
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
        service = await get_session_service()
        user_id = get_user_id(http_request, user_id)
        
        # 调用服务层列出会话
        sessions = await service.list_sessions(user_id=user_id, limit=limit, skip=skip)
        
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
        service = await get_session_service()
        user_id = get_user_id(http_request, request.user_id)
        
        # 调用服务层搜索会话
        sessions = await service.search_sessions(
            query=request.query,
            user_id=user_id,
            limit=request.limit
        )
        
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
        service = await get_session_service()
        user_id = get_user_id(http_request, user_id)
        
        # 调用服务层删除会话
        success = await service.delete_session(session_id, user_id=user_id)
        
        return JSONResponse(content={
            "success": success,
            "message": "会话删除成功" if success else "会话删除失败或不存在"
        })
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


class BatchDeleteRequest(BaseModel):
    """批量删除会话请求"""
    session_ids: list
    user_id: Optional[str] = None


@router.post("/batch/delete")
async def batch_delete_sessions(
    request: BatchDeleteRequest,
    http_request: Request
):
    """批量删除会话"""
    try:
        service = await get_session_service()
        user_id = get_user_id(http_request, request.user_id)
        
        if not request.session_ids or len(request.session_ids) == 0:
            raise HTTPException(status_code=400, detail="会话ID列表不能为空")
        
        # 调用服务层批量删除会话
        result = await service.delete_sessions(request.session_ids, user_id=user_id)
        
        return JSONResponse(content={
            "success": True,
            "data": result,
            "message": f"成功删除 {result['success_count']} 个会话，失败 {result['failed_count']} 个"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除会话失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量删除会话失败: {str(e)}")


@router.put("/{session_id}")
async def update_session(
    session_id: str,
    request: SaveSessionRequest,
    http_request: Request
):
    """
    更新会话数据
    
    如果提供了 imageDataUrl 且为 base64 格式，会自动上传到 OSS 并替换为 URL
    """
    try:
        service = await get_session_service()
        user_id = get_user_id(http_request, request.user_id)
        
        # 处理 imageDataUrl：如果是 base64 格式，上传到 OSS 并替换为 URL
        image_url = request.imageDataUrl
        if image_url and image_url.startswith("data:image/"):
            oss_url = await upload_base64_image_to_oss(image_url)
            if oss_url:
                image_url = oss_url
                logger.info(f"图片已上传到 OSS: {oss_url}")
            else:
                logger.warning(f"图片上传到 OSS 失败，保留原始 data URL")
        
        # 构建会话数据
        session_data = {
            "url": request.url,
            "title": request.title,
            "pageTitle": request.pageTitle,
            "pageDescription": request.pageDescription,
            "pageContent": request.pageContent,
            "messages": request.messages,
            "tags": request.tags,
            "updatedAt": request.updatedAt,
            "lastAccessTime": request.lastAccessTime
        }
        
        # 如果 imageDataUrl 已处理，添加到会话数据中
        if image_url:
            session_data["imageDataUrl"] = image_url
        
        # 调用服务层更新会话
        result = await service.update_session(session_id, session_data, user_id=user_id)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "session_id": result["session_id"],
                "id": result["id"]
            },
            "message": "会话更新成功"
        })
    except ValueError as e:
        # 会话不存在
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新会话失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新会话失败: {str(e)}")

