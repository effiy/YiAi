from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from typing import Any, Dict, List, Optional
from datetime import datetime
from config import settings

import logging
# 配置日志
logger = logging.getLogger(__name__)

from dotenv import load_dotenv # type: ignore
load_dotenv()

class MongoDB:
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._client:
            try:
                mongodb_url = settings.MONGODB_URL
                database_name = settings.MONGODB_DATABASE
                self._client = AsyncIOMotorClient(mongodb_url)
                self._db = self._client[database_name]
                logger.info(f"MongoDB 连接已初始化，数据库: {database_name}")
            except Exception as e:
                logger.error(f"MongoDB 连接初始化失败: {str(e)}")
                raise

    @property
    def db(self):
        return self._db

    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """插入单个文档"""
        if 'createdTime' not in document:
            document['createdTime'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        result = await self._db[collection_name].insert_one(document)
        return str(result.inserted_id)

    async def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """插入多个文档"""
        for document in documents:
            if 'createdTime' not in document:
                document['createdTime'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        result = await self._db[collection_name].insert_many(documents)
        return [str(id) for id in result.inserted_ids]

    async def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找单个文档"""
        return await self._db[collection_name].find_one(query)

    async def find_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """查找多个文档"""
        cursor = self._db[collection_name].find(query).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        return await cursor.to_list(length=limit)

    async def update_one(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """更新单个文档"""
        result = await self._db[collection_name].update_one(query, {"$set": update})
        return result.modified_count

    async def update_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """更新多个文档"""
        result = await self._db[collection_name].update_many(query, {"$set": update})
        return result.modified_count

    async def delete_one(self, collection_name: str, query: Dict[str, Any]) -> int:
        """删除单个文档"""
        result = await self._db[collection_name].delete_one(query)
        return result.deleted_count

    async def delete_many(self, collection_name: str, query: Dict[str, Any]) -> int:
        """删除多个文档"""
        result = await self._db[collection_name].delete_many(query)
        return result.deleted_count

    async def count_documents(self, collection_name: str, query: Dict[str, Any]) -> int:
        """统计文档数量"""
        return await self._db[collection_name].count_documents(query)

    async def aggregate(
        self,
        collection_name: str,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """聚合查询"""
        return await self._db[collection_name].aggregate(pipeline).to_list(None)

    def get_collection(self, collection_name: str):
        """获取集合对象"""
        return self._db[collection_name]

    async def create_index(
        self,
        collection_name: str,
        keys: List[tuple],
        unique: bool = False
    ):
        """创建索引"""
        await self._db[collection_name].create_index(keys, unique=unique)

    async def close(self):
        """关闭数据库连接"""
        if self._client:
            self._client.close()
            logger.info("MongoDB 连接已关闭")

    async def find_one_and_delete(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找并删除单个文档"""
        result = await self._db[collection_name].find_one_and_delete(query)
        return result

    async def find_one_and_update(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        return_document: bool = False
    ) -> Optional[Dict[str, Any]]:
        """查找并更新单个文档"""
        result = await self._db[collection_name].find_one_and_update(
            query,
            {"$set": update},
            return_document=ReturnDocument.AFTER if return_document else ReturnDocument.BEFORE
        )
        return result