import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase # type: ignore
from pymongo import ReturnDocument # type: ignore
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic
from datetime import datetime, UTC
import logging
from dotenv import load_dotenv # type: ignore
from contextlib import asynccontextmanager

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()

T = TypeVar('T')

class MongoDB:
    _instance = None
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None
    _pool_size: int = 10
    _max_pool_size: int = 50

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._client:
            try:
                mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
                database_name = os.getenv("MONGODB_DATABASE", "ruiyi")
                
                # 配置连接池
                self._client = AsyncIOMotorClient(
                    mongodb_url,
                    maxPoolSize=self._max_pool_size,
                    minPoolSize=self._pool_size,
                    maxIdleTimeMS=30000,
                    waitQueueTimeoutMS=10000,
                    retryWrites=True,
                    retryReads=True
                )
                self._db = self._client[database_name]
                logger.info(f"MongoDB 连接已初始化，数据库: {database_name}")
            except Exception as e:
                logger.error(f"MongoDB 连接初始化失败: {str(e)}")
                raise

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if not self._db:
            raise RuntimeError("数据库连接未初始化")
        return self._db

    @asynccontextmanager
    async def get_collection(self, collection_name: str):
        """获取集合对象的上下文管理器"""
        try:
            collection = self.db[collection_name]
            yield collection
        except Exception as e:
            logger.error(f"获取集合 {collection_name} 失败: {str(e)}")
            raise

    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """插入单个文档"""
        try:
            if 'createdTime' not in document:
                document['createdTime'] = datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')
            async with self.get_collection(collection_name) as collection:
                result = await collection.insert_one(document)
                return str(result.inserted_id)
        except Exception as e:
            logger.error(f"插入文档失败: {str(e)}")
            raise

    async def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """插入多个文档"""
        try:
            for document in documents:
                if 'createdTime' not in document:
                    document['createdTime'] = datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')
            async with self.get_collection(collection_name) as collection:
                result = await collection.insert_many(documents)
                return [str(id) for id in result.inserted_ids]
        except Exception as e:
            logger.error(f"批量插入文档失败: {str(e)}")
            raise

    async def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找单个文档"""
        try:
            async with self.get_collection(collection_name) as collection:
                return await collection.find_one(query)
        except Exception as e:
            logger.error(f"查找文档失败: {str(e)}")
            raise

    async def find_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """查找多个文档"""
        try:
            async with self.get_collection(collection_name) as collection:
                cursor = collection.find(query).skip(skip).limit(limit)
                if sort:
                    cursor = cursor.sort(sort)
                return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"查找多个文档失败: {str(e)}")
            raise

    async def update_one(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """更新单个文档"""
        try:
            async with self.get_collection(collection_name) as collection:
                result = await collection.update_one(query, {"$set": update})
                return result.modified_count
        except Exception as e:
            logger.error(f"更新文档失败: {str(e)}")
            raise

    async def update_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """更新多个文档"""
        try:
            async with self.get_collection(collection_name) as collection:
                result = await collection.update_many(query, {"$set": update})
                return result.modified_count
        except Exception as e:
            logger.error(f"批量更新文档失败: {str(e)}")
            raise

    async def delete_one(self, collection_name: str, query: Dict[str, Any]) -> int:
        """删除单个文档"""
        try:
            async with self.get_collection(collection_name) as collection:
                result = await collection.delete_one(query)
                return result.deleted_count
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            raise

    async def delete_many(self, collection_name: str, query: Dict[str, Any]) -> int:
        """删除多个文档"""
        try:
            async with self.get_collection(collection_name) as collection:
                result = await collection.delete_many(query)
                return result.deleted_count
        except Exception as e:
            logger.error(f"批量删除文档失败: {str(e)}")
            raise

    async def count_documents(self, collection_name: str, query: Dict[str, Any]) -> int:
        """统计文档数量"""
        try:
            async with self.get_collection(collection_name) as collection:
                return await collection.count_documents(query)
        except Exception as e:
            logger.error(f"统计文档数量失败: {str(e)}")
            raise

    async def aggregate(
        self,
        collection_name: str,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """聚合查询"""
        try:
            async with self.get_collection(collection_name) as collection:
                return await collection.aggregate(pipeline).to_list(None)
        except Exception as e:
            logger.error(f"聚合查询失败: {str(e)}")
            raise

    async def create_index(
        self,
        collection_name: str,
        keys: List[tuple],
        unique: bool = False
    ):
        """创建索引"""
        try:
            async with self.get_collection(collection_name) as collection:
                await collection.create_index(keys, unique=unique)
        except Exception as e:
            logger.error(f"创建索引失败: {str(e)}")
            raise

    async def close(self):
        """关闭数据库连接"""
        if self._client:
            self._client.close()
            logger.info("MongoDB 连接已关闭")

    async def find_one_and_delete(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找并删除单个文档"""
        try:
            async with self.get_collection(collection_name) as collection:
                return await collection.find_one_and_delete(query)
        except Exception as e:
            logger.error(f"查找并删除文档失败: {str(e)}")
            raise

    async def find_one_and_update(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        return_document: bool = False
    ) -> Optional[Dict[str, Any]]:
        """查找并更新单个文档"""
        try:
            async with self.get_collection(collection_name) as collection:
                return await collection.find_one_and_update(
                    query,
                    {"$set": update},
                    return_document=ReturnDocument.AFTER if return_document else ReturnDocument.BEFORE
                )
        except Exception as e:
            logger.error(f"查找并更新文档失败: {str(e)}")
            raise

# 主函数，用于测试和演示MongoDB类的使用
async def main():
    """MongoDB类使用示例"""
    mongodb = None
    try:
        mongodb = MongoDB()
        logger.info("开始MongoDB测试...")
        
        # 创建测试集合
        test_collection = "test_collection"
        
        # 测试插入单个文档
        user_id = await mongodb.insert_one(
            test_collection,
            {"name": "张三", "age": 30, "email": "zhangsan@example.com"}
        )
        logger.info(f"插入用户ID: {user_id}")
        
        # 测试查找文档
        user = await mongodb.find_one(test_collection, {"name": "张三"})
        if user:
            logger.info(f"找到用户: {user['name']}, 邮箱: {user['email']}")
        
        # 测试更新文档
        modified_count = await mongodb.update_one(
            test_collection,
            {"name": "张三"},
            {"age": 31, "updated": True}
        )
        logger.info(f"更新的文档数: {modified_count}")
        
        # 测试查找并更新
        updated_user = await mongodb.find_one_and_update(
            test_collection,
            {"name": "张三"},
            {"status": "active"},
            return_document=True
        )
        if updated_user:
            logger.info(f"用户 {updated_user['name']} 状态已更新为: {updated_user.get('status')}")
        
        # 测试插入多个文档
        batch_ids = await mongodb.insert_many(
            test_collection,
            [
                {"name": "李四", "age": 25, "email": "lisi@example.com"},
                {"name": "王五", "age": 35, "email": "wangwu@example.com"}
            ]
        )
        logger.info(f"批量插入ID: {batch_ids}")
        
        # 测试查询多个文档
        users = await mongodb.find_many(
            test_collection,
            {"age": {"$gt": 25}},
            sort=[("age", -1)]
        )
        logger.info(f"找到 {len(users)} 个年龄大于25的用户")
        for user in users:
            logger.info(f"用户: {user['name']}, 年龄: {user['age']}")
        
        # 测试统计
        count = await mongodb.count_documents(test_collection, {})
        logger.info(f"总用户数: {count}")
        
        # 测试删除
        deleted = await mongodb.delete_many(test_collection, {})
        logger.info(f"清理测试数据，删除了 {deleted} 条记录")
        
        logger.info("MongoDB测试完成")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        if mongodb:
            await mongodb.close()

if __name__ == "__main__":
    import asyncio
    print("开始执行MongoDB测试...")
    asyncio.run(main())
    print("MongoDB测试执行完成！")