import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.database import db
from core.config import settings
from core.utils import get_current_time
from models.collections import STATE_RECORDS

logger = logging.getLogger(__name__)


class StateStoreService:
    """结构化状态存储服务"""

    def __init__(self) -> None:
        self.collection_name = settings.collection_state_records
        self.max_limit = settings.state_store_query_max_limit

    async def _ensure_initialized(self) -> None:
        await db.initialize()

    async def create(self, record: Dict[str, Any]) -> Dict[str, str]:
        """创建状态记录

        Args:
            record: 记录字典，应包含 record_type 等字段

        Returns:
            {"key": "..."}
        """
        await self._ensure_initialized()
        collection = db.db[self.collection_name]

        data = dict(record)
        data["key"] = data.get("key") or str(uuid.uuid4())
        now = get_current_time()
        data.setdefault("created_time", now)
        data.setdefault("updated_time", now)

        await collection.insert_one(data)
        logger.info(f"State record created: {data['key']} type={data.get('record_type')}")
        return {"key": data["key"]}

    async def query(
        self,
        record_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        title_contains: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        page_num: int = 1,
        page_size: int = 2000,
    ) -> Dict[str, Any]:
        """查询状态记录

        Returns:
            包含 list, total, pageNum, pageSize, totalPages 的字典
        """
        await self._ensure_initialized()
        collection = db.db[self.collection_name]

        page_size = min(page_size, self.max_limit)
        filter_dict: Dict[str, Any] = {}

        if record_type:
            filter_dict["record_type"] = record_type
        if tags:
            filter_dict["tags"] = {"$in": tags}
        if title_contains:
            filter_dict["title"] = {
                "$regex": f".*{title_contains}.*",
                "$options": "i",
            }
        if created_after or created_before:
            filter_dict["created_time"] = {}
            if created_after:
                filter_dict["created_time"]["$gte"] = created_after
            if created_before:
                filter_dict["created_time"]["$lt"] = created_before

        cursor = (
            collection.find(filter_dict, {"_id": 0})
            .sort("created_time", -1)
            .skip((page_num - 1) * page_size)
            .limit(page_size)
        )
        data = [doc async for doc in cursor]
        total = await collection.count_documents(filter_dict)
        total_pages = (total + page_size - 1) // page_size

        return {
            "list": data,
            "total": total,
            "pageNum": page_num,
            "pageSize": page_size,
            "totalPages": total_pages,
        }

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """根据 key 获取单条记录"""
        await self._ensure_initialized()
        collection = db.db[self.collection_name]
        return await collection.find_one({"key": key}, {"_id": 0})

    async def update(self, key: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新状态记录"""
        await self._ensure_initialized()
        collection = db.db[self.collection_name]

        update_data = dict(data)
        update_data.pop("key", None)
        update_data.pop("created_time", None)
        update_data["updated_time"] = get_current_time()

        result = await collection.update_one({"key": key}, {"$set": update_data})
        if result.matched_count == 0:
            raise ValueError(f"Record not found: {key}")
        return {"key": key, "updated": True}

    async def delete(self, key: str) -> Dict[str, Any]:
        """删除状态记录"""
        await self._ensure_initialized()
        collection = db.db[self.collection_name]
        result = await collection.delete_one({"key": key})
        if result.deleted_count == 0:
            raise ValueError(f"Record not found: {key}")
        return {"key": key, "deleted": True}
