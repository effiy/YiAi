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
        if self._client is None:
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
        if self._db is None:
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
        if self._client is not None:
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

# 创建全局单例MongoDB实例
mongodb_instance = MongoDB()

# 主函数，用于测试和演示MongoDB类的使用
async def insert_one(params: Dict[str, Any] = None) -> str:
    """测试插入单个文档
    
    Args:
        params: 参数字典，可包含：
            - cname: 集合名称，默认为"test_collection"
            - document: 要插入的文档，默认为测试数据
        
    Returns:
        str: 插入文档的ID
    """
    if params is None:
        params = {}
    
    cname = params.get("cname", "test_collection")
    document = params.get("document", {"name": "张三", "age": 30, "email": "zhangsan@example.com"})
    
    # 使用全局单例
    try:
        doc_id = await mongodb_instance.insert_one(
            cname,
            document
        )
        logger.info(f"插入文档ID: {doc_id}")
        return doc_id
    except Exception as e:
        logger.error(f"插入文档时出错: {e}")
        raise

async def find_one(params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """测试查找单个文档
    
    Args:
        params: 参数字典，可包含：
            - cname: 集合名称，默认为"test_collection"
            - query: 查询条件，默认查询名为"张三"的文档
            - projection: 指定返回的字段，默认为None（返回所有字段）
    
    Returns:
        Optional[Dict[str, Any]]: 查找到的文档
    """
    # 使用空字典作为默认值
    params = params or {}
    
    # 获取参数值
    cname = params.get("cname", "test_collection")
    query = params.get("query", {"name": "张三"})
    
    try:
        # 查询文档
        document = await mongodb_instance.find_one(
            collection_name=cname, 
            query=query if query else {}
        )
        
        # 增强日志输出
        if document:
            doc_id = document.get('_id', '未知ID')
            fields_info = [f"{k}: {v}" for k, v in document.items() if k != '_id']
            logger.info(f"查询成功: 文档ID[{doc_id}], "
                       f"包含字段和值: {', '.join(fields_info)}")
        else:
            logger.warning(f"未找到符合条件的文档: {query}")
        
        return document
    except Exception as e:
        logger.error(f"查找文档时出错: {e}")
        logger.exception("详细错误信息:")
        raise

async def update_one(params: Dict[str, Any] = None) -> int:
    """测试更新单个文档
    
    Args:
        params: 参数字典，可包含：
            - cname: 集合名称，默认为"test_collection"
            - query: 查询条件，默认查询名为"张三"的文档
            - update: 更新内容，默认更新年龄和添加updated标记
            
    Returns:
        int: 更新的文档数量
    """
    if params is None:
        params = {}
    
    cname = params.get("cname", "test_collection")
    query = params.get("query", {"name": "张三"})
    update = params.get("update", {"age": 31, "updated": True})
    
    try:
        modified_count = await mongodb_instance.update_one(
            cname,
            query,
            update
        )
        logger.info(f"更新的文档数: {modified_count}")
        return modified_count
    except Exception as e:
        logger.error(f"更新文档时出错: {e}")
        raise

async def find_one_and_update(params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """测试查找并更新文档
    
    Args:
        params: 参数字典，可包含：
            - cname: 集合名称，默认为"test_collection"
            - query: 查询条件，默认查询名为"张三"的文档
            - update: 更新内容，默认添加status字段
            - return_document: 是否返回更新后的文档，默认为True
            
    Returns:
        Optional[Dict[str, Any]]: 更新前或更新后的文档
    """
    if params is None:
        params = {}
    
    cname = params.get("cname", "test_collection")
    query = params.get("query", {"name": "张三"})
    update = params.get("update", {"status": "active"})
    return_document = params.get("return_document", True)
    
    try:
        updated_user = await mongodb_instance.find_one_and_update(
            cname,
            query,
            update,
            return_document=return_document
        )
        if updated_user:
            logger.info(f"用户 {updated_user['name']} 状态已更新为: {updated_user.get('status')}")
        return updated_user
    except Exception as e:
        logger.error(f"查找并更新文档时出错: {e}")
        raise

async def insert_many(params: Dict[str, Any] = None) -> List[str]:
    """测试插入多个文档
    
    Args:
        params: 参数字典，可包含：
            - cname: 集合名称，默认为"test_collection"
            - documents: 要插入的文档列表，默认为测试数据
            
    Returns:
        List[str]: 插入文档的ID列表
    """
    if params is None:
        params = {}
    
    cname = params.get("cname", "test_collection")
    documents = params.get("documents", [
        {"name": "李四", "age": 25, "email": "lisi@example.com"},
        {"name": "王五", "age": 35, "email": "wangwu@example.com"}
    ])
    
    try:
        batch_ids = await mongodb_instance.insert_many(
            cname,
            documents
        )
        logger.info(f"批量插入ID: {batch_ids}")
        return batch_ids
    except Exception as e:
        logger.error(f"批量插入文档时出错: {e}")
        raise

async def find_many(params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """测试查询多个文档
    
    Args:
        params: 参数字典，可包含：
            - cname: 集合名称，默认为"test_collection"
            - query: 查询条件，默认查询年龄大于25的文档
            - sort: 排序条件，默认按年龄降序排列
            
    Returns:
        List[Dict[str, Any]]: 查询到的文档列表
    """
    if params is None:
        params = {}
    
    cname = params.get("cname", "test_collection")
    query = params.get("query", {"age": {"$gt": 25}})
    sort = params.get("sort", [("age", -1)])
    
    try:
        users = await mongodb_instance.find_many(
            cname,
            query,
            sort=sort
        )
        logger.info(f"找到 {len(users)} 个符合条件的用户")
        for user in users:
            logger.info(f"用户: {user['name']}, 年龄: {user['age']}")
        return users
    except Exception as e:
        logger.error(f"查询多个文档时出错: {e}")
        raise

async def count_documents(params: Dict[str, Any] = None) -> int:
    """测试文档计数
    
    Args:
        params: 参数字典，可包含：
            - cname: 集合名称，默认为"test_collection"
            - query: 查询条件，默认查询所有文档
            
    Returns:
        int: 文档数量
    """
    if params is None:
        params = {}
    
    cname = params.get("cname", "test_collection")
    query = params.get("query", {})
    
    try:
        count = await mongodb_instance.count_documents(cname, query)
        logger.info(f"总文档数: {count}")
        return count
    except Exception as e:
        logger.error(f"统计文档数量时出错: {e}")
        raise

async def delete_many(params: Dict[str, Any] = None) -> int:
    """测试删除多个文档
    
    Args:
        params: 参数字典，可包含：
            - cname: 集合名称，默认为"test_collection"
            - query: 查询条件，默认删除所有文档
            
    Returns:
        int: 删除的文档数量
    """
    if params is None:
        params = {}
    
    cname = params.get("cname", "test_collection")
    query = params.get("query", {})
    
    try:
        deleted = await mongodb_instance.delete_many(cname, query)
        logger.info(f"清理测试数据，删除了 {deleted} 条记录")
        return deleted
    except Exception as e:
        logger.error(f"删除多个文档时出错: {e}")
        raise

async def main(params: Dict[str, Any] = None):
    """MongoDB类使用示例
    
    Args:
        params: 参数字典，可选
    """
    logger.info("开始MongoDB测试...")
    
    try:
        # 执行各个测试函数
        # await insert_one(params)
        await find_one(params)
        # await update_one(params)
        # await find_one_and_update(params)
        # await insert_many(params)
        # await find_many(params)
        # await count_documents(params)
        # await delete_many(params)
        
        logger.info("MongoDB测试完成")
        return {"status": "success", "message": "MongoDB测试完成"}
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import asyncio
    print("开始执行MongoDB测试...")
    result = asyncio.run(main())
    print(f"MongoDB测试执行完成！结果: {result}")