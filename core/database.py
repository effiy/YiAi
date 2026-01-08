"""MongoDB 数据访问层（单例）
- 管理连接、索引、常用 CRUD 包装
"""
import os
import logging
from typing import Optional, List, Dict, Any, TypeVar
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from core.settings import settings

logger = logging.getLogger(__name__)

class MongoDB:
    """
    MongoDB Database Handler (Singleton)
    """
    _instance: Optional['MongoDB'] = None
    _client: Optional[AsyncIOMotorClient] = None
    _db = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance

    async def initialize(self):
        """
        Initialize database connection and indexes
        
        Example:
            >>> await db.initialize()
        """
        if self._initialized:
            return

        if self._client is None:
            try:
                mongodb_url = settings.mongodb_url
                database_name = settings.mongodb_db_name
                
                # Configure connection pool
                self._client = AsyncIOMotorClient(
                    mongodb_url,
                    maxPoolSize=settings.mongodb_max_pool_size,
                    minPoolSize=settings.mongodb_pool_size,
                    maxIdleTimeMS=30000,
                    waitQueueTimeoutMS=10000,
                    retryWrites=True,
                    retryReads=True
                )
                self._db = self._client[database_name]
                logger.info(f"MongoDB connected: {database_name}")
                
                # Ensure indexes
                await self._ensure_indexes()
                
                self._initialized = True
            except Exception as e:
                logger.error(f"MongoDB initialization failed: {str(e)}")
                raise

    async def close(self):
        """
        Close database connection
        
        Example:
            >>> await db.close()
        """
        if self._client:
            self._client.close()
            self._client = None
            self._initialized = False
            logger.info("MongoDB connection closed")

    @property
    def db(self):
        if self._db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._db

    async def _ensure_indexes(self):
        """
        Create necessary indexes
        
        Example:
            >>> await self._ensure_indexes()
        """
        try:
            # RSS Link Unique Index
            await self._ensure_unique_index(settings.collection_rss, 'link')
        except Exception as e:
            logger.error(f"Index creation failed: {str(e)}")

    async def _ensure_unique_index(self, collection_name: str, field: str):
        collection = self.db[collection_name]
        await collection.create_index([(field, 1)], unique=True, background=True)
        logger.info(f"Ensured unique index for {collection_name}.{field}")

    # Helper methods wrapper
    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """
        Insert a single document
        
        Args:
            collection_name: Collection name
            document: Document to insert
            
        Returns:
            str: Inserted document ID
            
        Example:
            >>> id = await db.insert_one("users", {"name": "test"})
        """
        if 'createdTime' not in document:
            document['createdTime'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        result = await self.db[collection_name].insert_one(document)
        return str(result.inserted_id)

    async def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple documents
        
        Args:
            collection_name: Collection name
            documents: List of documents to insert
            
        Returns:
            List[str]: List of inserted document IDs
            
        Example:
            >>> ids = await db.insert_many("users", [{"name": "test1"}, {"name": "test2"}])
        """
        for doc in documents:
            if 'createdTime' not in doc:
                doc['createdTime'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        result = await self.db[collection_name].insert_many(documents)
        return [str(id) for id in result.inserted_ids]

    async def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a single document
        
        Args:
            collection_name: Collection name
            query: Query criteria
            
        Returns:
            Optional[Dict[str, Any]]: Found document or None
            
        Example:
            >>> user = await db.find_one("users", {"name": "test"})
        """
        return await self.db[collection_name].find_one(query)

# Global instance
db = MongoDB()

