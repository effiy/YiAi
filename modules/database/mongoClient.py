import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from typing import Any, Dict, List, Optional, TypeVar
from datetime import datetime, timezone
import logging
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import asyncio

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()

T = TypeVar('T')

class MongoClient:
    _instance = None
    _client: Optional[AsyncIOMotorClient] = None
    _db = None
    _pool_size: int = 10
    _max_pool_size: int = 50

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoClient, cls).__new__(cls)
        return cls._instance

    async def initialize(self):
        """初始化数据库连接"""
        if self._client is None:
            # 双重检查锁定模式，避免多次初始化
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
                    logger.info(f"MongoClient 连接已初始化，数据库: {database_name}")
                except Exception as e:
                    logger.error(f"MongoClient 连接初始化失败: {str(e)}")
                    raise

    def __init__(self):
        # 不再在同步初始化方法中创建连接
        pass

    @property
    def db(self):
        if self._db is None:
            raise RuntimeError("数据库连接未初始化，请先调用 initialize()")
        return self._db

    @asynccontextmanager
    async def get_collection(self, collection_name: str):
        """获取集合对象的异步上下文管理器"""
        # 确保数据库已初始化
        await self.initialize()
        
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
                document['createdTime'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            collection = self.db[collection_name]
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
                    document['createdTime'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            collection = self.db[collection_name]
            result = await collection.insert_many(documents)
            return [str(id) for id in result.inserted_ids]
        except Exception as e:
            logger.error(f"批量插入文档失败: {str(e)}")
            raise

    async def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找单个文档"""
        try:
            collection = self.db[collection_name]
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
            collection = self.db[collection_name]
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
            collection = self.db[collection_name]
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
            collection = self.db[collection_name]
            result = await collection.update_many(query, {"$set": update})
            return result.modified_count
        except Exception as e:
            logger.error(f"批量更新文档失败: {str(e)}")
            raise

    async def delete_one(self, collection_name: str, query: Dict[str, Any]) -> int:
        """删除单个文档"""
        try:
            collection = self.db[collection_name]
            result = await collection.delete_one(query)
            return result.deleted_count
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            raise

    async def delete_many(self, collection_name: str, query: Dict[str, Any]) -> int:
        """删除多个文档"""
        try:
            collection = self.db[collection_name]
            result = await collection.delete_many(query)
            return result.deleted_count
        except Exception as e:
            logger.error(f"批量删除文档失败: {str(e)}")
            raise

    async def count_documents(self, collection_name: str, query: Dict[str, Any]) -> int:
        """统计文档数量"""
        try:
            collection = self.db[collection_name]
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
            collection = self.db[collection_name]
            cursor = collection.aggregate(pipeline)
            return await cursor.to_list(length=None)
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
            collection = self.db[collection_name]
            await collection.create_index(keys, unique=unique)
        except Exception as e:
            logger.error(f"创建索引失败: {str(e)}")
            raise

    async def close(self):
        """关闭数据库连接"""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoClient 连接已关闭")

    async def find_one_and_delete(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找并删除单个文档"""
        try:
            collection = self.db[collection_name]
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
            collection = self.db[collection_name]
            return await collection.find_one_and_update(
                query,
                {"$set": update},
                return_document=ReturnDocument.AFTER if return_document else ReturnDocument.BEFORE
            )
        except Exception as e:
            logger.error(f"查找并更新文档失败: {str(e)}")
            raise

async def insert_one(params: Dict[str, Any] = None) -> str:

    if params is None:
        params = {}

    cname = params.get("cname", "test_collection")
    document = params.get("document", {"name": "张三", "age": 30, "email": "zhangsan@example.com"})

    # 使用全局单例
    mongodb_instance = MongoClient()
    try:
        # 确保数据库已初始化
        await mongodb_instance.initialize()

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
    # 使用空字典作为默认值
    params = params or {}

    # 获取参数值
    cname = params.get("cname", "test_collection")
    query = params.get("query", {"name": "张三"})

    try:
        mongodb_instance = MongoClient()
        await mongodb_instance.initialize()

        document = await mongodb_instance.find_one(
            collection_name=cname,
            query=query if query else {}
        )

        # 增强日志输出
        if document:
            # 将 ObjectId 转换为字符串
            if '_id' in document:
                document['_id'] = str(document['_id'])
            doc_id = document.get('_id', '未知ID')
            fields_info = [f"{k}: {v}" for k, v in document.items() if k != '_id']
            logger.info(f"查询成功: 文档ID[{doc_id}], "
                       f"包含字段和值: {', '.join(fields_info)}")
        else:
            logger.warning(f"未找到符合条件的文档: {query}")

        logger.info(f"查询结果: {document}")
        return document
    except Exception as e:
        logger.error(f"查找文档时出错: {e}")
        logger.exception("详细错误信息:")
        raise

async def update_one(params: Dict[str, Any] = None) -> int:

    if params is None:
        params = {}

    cname = params.get("cname", "test_collection")
    query = params.get("query", {"name": "张三"})
    update = params.get("update", {"age": 31, "updated": True})

    mongodb_instance = MongoClient()
    try:
        # 确保数据库已初始化
        await mongodb_instance.initialize()

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

    if params is None:
        params = {}

    cname = params.get("cname", "test_collection")
    query = params.get("query", {"name": "张三"})
    update = params.get("update", {"status": "active"})
    return_document = params.get("return_document", True)

    mongodb_instance = MongoClient()
    try:
        # 确保数据库已初始化
        await mongodb_instance.initialize()

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

    if params is None:
        params = {}

    cname = params.get("cname", "test_collection")
    documents = params.get("documents", [
        {"name": "李四", "age": 25, "email": "lisi@example.com"},
        {"name": "王五", "age": 35, "email": "wangwu@example.com"}
    ])

    mongodb_instance = MongoClient()
    try:
        # 确保数据库已初始化
        await mongodb_instance.initialize()

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
    
    if params is None:
        params = {}

    collection_name = params.get("collection_name", "test_collection")
    filter_query = params.get("filter_query", {"age": {"$gt": 25}})
    sort_criteria = params.get("sort_criteria", [["age", -1]])

    # 将列表格式的排序条件转换为元组格式
    sort_criteria = [tuple(criteria) for criteria in sort_criteria]

    db_instance = MongoClient()
    try:
        # 确保数据库已初始化
        await db_instance.initialize()

        documents = await db_instance.find_many(
            collection_name,
            filter_query,
            sort=sort_criteria
        )

        # 将 ObjectId 转换为字符串
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])

        logger.info(f"找到 {len(documents)} 个符合条件的文档")
        for doc in documents:
            logger.info(f"文档: {doc}")
        return documents
    except Exception as e:
        logger.error(f"查询多个文档时出错: {e}")
        raise

"""测试文档计数

Args:
    params: 参数字典，可包含：
        - cname: 集合名称，默认为"test_collection"
        - query: 查询条件，默认查询所有文档

Returns:
    int: 文档数量
"""
async def count_documents(params: Dict[str, Any] = None) -> int:

    if params is None:
        params = {}

    cname = params.get("cname", "test_collection")
    query = params.get("query", {})

    mongodb_instance = MongoClient()
    try:
        # 确保数据库已初始化
        await mongodb_instance.initialize()

        count = await mongodb_instance.count_documents(cname, query)
        logger.info(f"总文档数: {count}")
        return count
    except Exception as e:
        logger.error(f"统计文档数量时出错: {e}")
        raise


async def delete_many(params: Dict[str, Any] = None) -> int:
    if params is None:
        params = {}

    cname = params.get("cname", "test_collection")
    query = params.get("query", {})

    mongodb_instance = MongoClient()
    try:
        # 确保数据库已初始化
        await mongodb_instance.initialize()

        deleted = await mongodb_instance.delete_many(cname, query)
        logger.info(f"清理测试数据，删除了 {deleted} 条记录")
        return deleted
    except Exception as e:
        logger.error(f"删除多个文档时出错: {e}")
        raise

async def upsert(params: Dict[str, Any] = None) -> Dict[str, Any]:
    params = params or {}

    cname = params.get("cname", "test_collection")
    document = params.get("document", {"name": "张三", "age": 31, "email": "zhangsan_new@example.com"})
    query_fields = params.get("query_fields", ["name"])

    # 从文档中提取查询条件
    query = {}
    for field in query_fields:
        if field in document:
            query[field] = document[field]

    # 如果没有找到任何查询字段，则使用整个文档作为查询条件
    if not query:
        query = document

    # 更新内容就是整个文档
    update = {"$set": document}

    mongodb_instance = MongoClient()
    try:
        # 确保数据库已初始化
        await mongodb_instance.initialize()

        # 获取集合对象
        collection = mongodb_instance._db[cname]

        # 执行upsert操作
        result = await collection.update_one(
            query,
            update,
            upsert=True
        )

        response = {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None,
            "is_new": result.upserted_id is not None
        }

        if result.upserted_id:
            logger.info(f"文档已插入，ID: {result.upserted_id}")
        else:
            logger.info(f"文档已更新，匹配数: {result.matched_count}, 修改数: {result.modified_count}")

        return response
    except Exception as e:
        logger.error(f"upsert操作时出错: {e}")
        logger.exception("详细错误信息:")
        raise

async def upsert_many(params: Dict[str, Any] = None) -> Dict[str, Any]:
    params = params or {}

    cname = params.get("cname", "test_collection")
    documents = params.get("documents", [
        {"name": "张三", "age": 31},
        {"name": "李四", "email": "lisi_new@example.com"}
    ])
    query_fields = params.get("query_fields", ["name"])

    mongodb_instance = MongoClient()
    try:
        # 确保数据库已初始化
        await mongodb_instance.initialize()

        # 获取集合对象
        collection = mongodb_instance._db[cname]

        results = {
            "matched_count": 0,
            "modified_count": 0,
            "upserted_ids": [],
            "new_count": 0
        }

        # 执行批量upsert操作
        for doc in documents:
            # 从文档中提取查询条件
            query = {}
            for field in query_fields:
                if field in doc:
                    query[field] = doc[field]

            # 如果没有找到任何查询字段，则使用整个文档作为查询条件
            if not query:
                query = doc

            # 更新内容就是整个文档
            update = {"$set": doc}

            result = await collection.update_one(
                query,
                update,
                upsert=True
            )

            results["matched_count"] += result.matched_count
            results["modified_count"] += result.modified_count

            if result.upserted_id:
                results["upserted_ids"].append(str(result.upserted_id))
                results["new_count"] += 1

        logger.info(f"批量upsert完成: 匹配数: {results['matched_count']}, "
                   f"修改数: {results['modified_count']}, "
                   f"新插入数: {results['new_count']}")

        return results
    except Exception as e:
        logger.error(f"批量upsert操作时出错: {e}")
        logger.exception("详细错误信息:")
        raise

async def list_collections(params: Dict[str, Any] = None) -> List[str]:
    if params is None:
        params = {}

    mongodb_instance = MongoClient()
    try:
        # 确保数据库已初始化
        await mongodb_instance.initialize()

        collections = await mongodb_instance._db.list_collection_names()
        logger.info(f"获取到 {len(collections)} 个集合")
        return collections
    except Exception as e:
        logger.error(f"获取集合列表时出错: {e}")
        raise

async def main(params: Dict[str, Any] = None):
    logger.info("开始MongoClient测试...")
    
    try:
        # 执行各个测试函数
        # await insert_one(params)
        document = await find_one(params)
        # await update_one(params)
        # await find_one_and_update(params)
        # await insert_many(params)
        # await find_many(params)
        # await count_documents(params)
        # await delete_many(params)
        
        logger.info("MongoClient测试完成")
        return {"status": "success", "message": "MongoClient测试完成", "document": document}
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    print("开始执行MongoClient测试...")
    
    mongodb = MongoClient()
    try:
        asyncio.run(mongodb.initialize())
        result = asyncio.run(main())
        print(f"MongoClient测试执行完成！结果: {result}")
    finally:
        # 确保关闭MongoClient连接
        asyncio.run(mongodb.close())
