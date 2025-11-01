import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from modules.database.mem0Client import Mem0Client

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/mem0",
    tags=["Mem0 Memory Management"],
    responses={404: {"description": "未找到"}},
)

# 初始化 Mem0 客户端
mem0_client = Mem0Client()


def get_user_id(request: Request, user_id: Optional[str] = None) -> str:
    """获取用户ID，优先级：参数 > X-User 请求头 > 默认值 bigboom"""
    if user_id:
        return user_id
    
    x_user = request.headers.get("X-User", "")
    if x_user:
        return x_user
    
    return "bigboom"


class AddMemoryRequest(BaseModel):
    memory: str
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchMemoryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    limit: int = 10
    metadata: Optional[Dict[str, Any]] = None


class UpdateMemoryRequest(BaseModel):
    memory: str
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.get("/status")
async def get_status():
    """检查 Mem0 服务状态"""
    return {
        "available": mem0_client.is_available(),
        "message": "Mem0 服务可用" if mem0_client.is_available() else "Mem0 服务不可用，请检查 Qdrant 和 Ollama 服务"
    }


@router.post("/memory")
async def add_memory(request: AddMemoryRequest, http_request: Request):
    """添加记忆"""
    try:
        if not mem0_client.is_available():
            raise HTTPException(status_code=503, detail="Mem0 服务不可用")
        
        user_id = get_user_id(http_request, request.user_id)
        
        result = mem0_client.add_memory(
            memory=request.memory,
            user_id=user_id,
            metadata=request.metadata
        )
        
        return JSONResponse(content={
            "success": True,
            "data": result,
            "message": "记忆添加成功"
        })
    except Exception as e:
        logger.error(f"添加记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加记忆失败: {str(e)}")


@router.post("/memory/search")
async def search_memories(request: SearchMemoryRequest, http_request: Request):
    """搜索相关记忆"""
    try:
        if not mem0_client.is_available():
            raise HTTPException(status_code=503, detail="Mem0 服务不可用")
        
        user_id = get_user_id(http_request, request.user_id)
        
        results = mem0_client.search_memories(
            query=request.query,
            user_id=user_id,
            limit=request.limit,
            metadata=request.metadata
        )
        
        return JSONResponse(content={
            "success": True,
            "count": len(results),
            "results": results,
            "message": f"找到 {len(results)} 条相关记忆"
        })
    except Exception as e:
        logger.error(f"搜索记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索记忆失败: {str(e)}")


@router.get("/memory")
async def get_memories(
    http_request: Request,
    user_id: Optional[str] = None,
    limit: int = 100
):
    """获取所有记忆"""
    try:
        if not mem0_client.is_available():
            raise HTTPException(status_code=503, detail="Mem0 服务不可用")
        
        user_id = get_user_id(http_request, user_id)
        
        memories = mem0_client.get_memories(
            user_id=user_id,
            limit=limit
        )
        
        # 确保 memories 是列表
        if memories is None:
            memories = []
        
        return JSONResponse(content={
            "success": True,
            "count": len(memories),
            "memories": memories,
            "message": f"获取到 {len(memories)} 条记忆"
        })
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e) if str(e) else repr(e)
        logger.error(f"获取记忆失败: {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取记忆失败: {error_msg}")


@router.put("/memory/{memory_id}")
async def update_memory(
    memory_id: str,
    request: UpdateMemoryRequest,
    http_request: Request
):
    """更新记忆"""
    try:
        if not mem0_client.is_available():
            raise HTTPException(status_code=503, detail="Mem0 服务不可用")
        
        user_id = get_user_id(http_request, request.user_id)
        
        result = mem0_client.update_memory(
            memory_id=memory_id,
            memory=request.memory,
            user_id=user_id,
            metadata=request.metadata
        )
        
        return JSONResponse(content={
            "success": True,
            "data": result,
            "message": "记忆更新成功"
        })
    except Exception as e:
        logger.error(f"更新记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新记忆失败: {str(e)}")


@router.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: str,
    http_request: Request,
    user_id: Optional[str] = None
):
    """删除记忆"""
    try:
        if not mem0_client.is_available():
            raise HTTPException(status_code=503, detail="Mem0 服务不可用")
        
        user_id = get_user_id(http_request, user_id)
        
        success = mem0_client.delete_memory(
            memory_id=memory_id,
            user_id=user_id
        )
        
        return JSONResponse(content={
            "success": success,
            "message": "记忆删除成功" if success else "记忆删除失败"
        })
    except Exception as e:
        logger.error(f"删除记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除记忆失败: {str(e)}")


@router.delete("/memory")
async def delete_all_memories(http_request: Request, user_id: Optional[str] = None):
    """删除所有记忆"""
    try:
        if not mem0_client.is_available():
            raise HTTPException(status_code=503, detail="Mem0 服务不可用")
        
        user_id = get_user_id(http_request, user_id)
        
        success = mem0_client.delete_all_memories(user_id=user_id)
        
        return JSONResponse(content={
            "success": success,
            "message": f"用户 {user_id} 的所有记忆删除成功" if success else "删除失败"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除所有记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除所有记忆失败: {str(e)}")

