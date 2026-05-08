import logging
from typing import Optional
from fastapi import APIRouter, Query

from models.schemas import StateRecord, StateQueryRequest
from services.state.state_service import StateStoreService
from core.error_codes import ErrorCode
from core.exceptions import BusinessException
from core.response import success

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/state", tags=["State"])

# 懒加载服务实例
_state_service: StateStoreService | None = None


def _get_service() -> StateStoreService:
    global _state_service
    if _state_service is None:
        _state_service = StateStoreService()
    return _state_service


@router.post("/records", status_code=201, operation_id="create_state_record")
async def create_record(record: StateRecord):
    """创建状态记录"""
    service = _get_service()
    data = record.model_dump(exclude_unset=True)
    # 如果 key 为空，让服务层生成
    if not data.get("key"):
        data.pop("key", None)
    result = await service.create(data)
    return success(data=result)


@router.get("/records", operation_id="query_state_records")
async def query_records(
    record_type: Optional[str] = Query(None),
    tags: Optional[list[str]] = Query(None),
    title_contains: Optional[str] = Query(None),
    created_after: Optional[str] = Query(None),
    created_before: Optional[str] = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(2000, ge=1, le=8000),
):
    """查询状态记录"""
    service = _get_service()
    result = await service.query(
        record_type=record_type,
        tags=tags,
        title_contains=title_contains,
        created_after=created_after,
        created_before=created_before,
        page_num=page_num,
        page_size=page_size,
    )
    return success(data=result)


@router.get("/records/{key}", operation_id="get_state_record")
async def get_record(key: str):
    """根据 key 获取单条记录"""
    service = _get_service()
    record = await service.get(key)
    if not record:
        raise BusinessException(ErrorCode.DATA_NOT_FOUND, message="Record not found")
    return success(data=record)


@router.put("/records/{key}", operation_id="update_state_record")
async def update_record(key: str, record: StateRecord):
    """更新状态记录"""
    service = _get_service()
    try:
        data = record.model_dump(exclude_unset=True)
        return success(data=await service.update(key, data))
    except ValueError as e:
        raise BusinessException(ErrorCode.DATA_NOT_FOUND, message=str(e))


@router.delete("/records/{key}", operation_id="delete_state_record")
async def delete_record(key: str):
    """删除状态记录"""
    service = _get_service()
    try:
        return success(data=await service.delete(key))
    except ValueError as e:
        raise BusinessException(ErrorCode.DATA_NOT_FOUND, message=str(e))
