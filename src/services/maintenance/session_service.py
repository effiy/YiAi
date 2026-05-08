"""Sessions 维护服务层 — 封装数据库访问，供 routes 调用"""
import logging
from typing import List, Dict, Any
from core.database import db
from core.config import settings

logger = logging.getLogger(__name__)


async def get_all_sessions() -> List[Dict[str, Any]]:
    """获取所有 sessions 文档"""
    await db.initialize()
    collection = db.db[settings.collection_sessions]
    sessions = []
    cursor = collection.find({})
    async for doc in cursor:
        sessions.append(doc)
    return sessions


async def delete_session_by_key(session_key: str) -> int:
    """按 key 删除单个 session，返回删除数量"""
    await db.initialize()
    collection = db.db[settings.collection_sessions]
    result = await collection.delete_one({'key': session_key})
    return result.deleted_count
