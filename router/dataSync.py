import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from modules.services.dataSyncService import DataSyncService
from router.utils import get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/data-sync",
    tags=["YiPet Data Sync"],
    responses={404: {"description": "未找到"}},
)

# 初始化数据同步服务（延迟初始化）
data_sync_service = None


async def get_data_sync_service():
    """获取数据同步服务实例（延迟初始化）"""
    global data_sync_service
    if data_sync_service is None:
        data_sync_service = DataSyncService()
        await data_sync_service.initialize()
    return data_sync_service

class SaveDataRequest(BaseModel):
    """保存数据请求"""
    data_type: str
    data: Dict[str, Any]
    user_id: Optional[str] = None


class BatchSaveDataRequest(BaseModel):
    """批量保存数据请求"""
    data_dict: Dict[str, Any]
    user_id: Optional[str] = None


@router.post("/save")
async def save_data(request: SaveDataRequest, http_request: Request):
    """保存YiPet数据到后端"""
    try:
        service = await get_data_sync_service()
        user_id = get_user_id(http_request, request.user_id)
        
        result = await service.save_data(
            user_id=user_id,
            data_type=request.data_type,
            data=request.data
        )
        
        return JSONResponse(content={
            "success": True,
            "data": result,
            "message": "数据保存成功"
        })
    except Exception as e:
        logger.error(f"保存数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"保存数据失败: {str(e)}")


@router.post("/batch-save")
async def batch_save_data(request: BatchSaveDataRequest, http_request: Request):
    """批量保存YiPet数据到后端"""
    try:
        service = await get_data_sync_service()
        user_id = get_user_id(http_request, request.user_id)
        
        result = await service.batch_save_data(
            user_id=user_id,
            data_dict=request.data_dict
        )
        
        return JSONResponse(content={
            "success": True,
            "data": result,
            "message": "批量保存数据成功"
        })
    except Exception as e:
        logger.error(f"批量保存数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量保存数据失败: {str(e)}")


@router.get("/{data_type}")
async def get_data(
    data_type: str,
    http_request: Request,
    user_id: Optional[str] = None
):
    """根据数据类型获取数据"""
    try:
        service = await get_data_sync_service()
        user_id = get_user_id(http_request, user_id)
        
        data = await service.get_data(
            user_id=user_id,
            data_type=data_type
        )
        
        if data is None:
            raise HTTPException(status_code=404, detail=f"数据类型 {data_type} 不存在")
        
        return JSONResponse(content={
            "success": True,
            "data": data,
            "data_type": data_type,
            "message": "获取数据成功"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")


@router.get("/")
async def get_all_data(
    http_request: Request,
    user_id: Optional[str] = None
):
    """获取用户的所有同步数据"""
    try:
        service = await get_data_sync_service()
        user_id = get_user_id(http_request, user_id)
        
        data_dict = await service.get_all_data(user_id=user_id)
        
        return JSONResponse(content={
            "success": True,
            "data": data_dict,
            "count": len(data_dict),
            "message": f"获取到 {len(data_dict)} 种类型的数据"
        })
    except Exception as e:
        logger.error(f"获取所有数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取所有数据失败: {str(e)}")


@router.delete("/{data_type}")
async def delete_data(
    data_type: str,
    http_request: Request,
    user_id: Optional[str] = None
):
    """删除指定类型的数据"""
    try:
        service = await get_data_sync_service()
        user_id = get_user_id(http_request, user_id)
        
        success = await service.delete_data(
            user_id=user_id,
            data_type=data_type
        )
        
        return JSONResponse(content={
            "success": success,
            "message": "数据删除成功" if success else "数据删除失败或不存在"
        })
    except Exception as e:
        logger.error(f"删除数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除数据失败: {str(e)}")


@router.delete("/")
async def delete_all_data(
    http_request: Request,
    user_id: Optional[str] = None
):
    """删除用户的所有同步数据"""
    try:
        service = await get_data_sync_service()
        user_id = get_user_id(http_request, user_id)
        
        success = await service.delete_data(
            user_id=user_id,
            data_type=None
        )
        
        return JSONResponse(content={
            "success": success,
            "message": "所有数据删除成功" if success else "删除失败或数据不存在"
        })
    except Exception as e:
        logger.error(f"删除所有数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除所有数据失败: {str(e)}")

