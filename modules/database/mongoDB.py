import os
from pymongo import MongoClient, ReturnDocument # type: ignore
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic
from datetime import datetime, timezone
import logging
from dotenv import load_dotenv # type: ignore
from contextlib import contextmanager

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
    _client: Optional[MongoClient] = None
    _db = None
    _pool_size: int = 10
    _max_pool_size: int = 50

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance

    def initialize(self):
        """初始化数据库连接"""
        if self._client is None:
            # 双重检查锁定模式，避免多次初始化
            if self._client is None:
                try:
                    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
                    database_name = os.getenv("MONGODB_DATABASE", "ruiyi")
                    
                    # 配置连接池
                    self._client = MongoClient(
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

    def __init__(self):
        # 不再在同步初始化方法中创建连接
        pass

    @property
    def db(self):
        if self._db is None:
            raise RuntimeError("数据库连接未初始化，请先调用 initialize()")
        return self._db

    @contextmanager
    def get_collection(self, collection_name: str):
        """获取集合对象的上下文管理器"""
        # 确保数据库已初始化
        self.initialize()
        
        try:
            collection = self.db[collection_name]
            yield collection
        except Exception as e:
            logger.error(f"获取集合 {collection_name} 失败: {str(e)}")
            raise

    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """插入单个文档"""
        try:
            if 'createdTime' not in document:
                document['createdTime'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            with self.get_collection(collection_name) as collection:
                result = collection.insert_one(document)
                return str(result.inserted_id)
        except Exception as e:
            logger.error(f"插入文档失败: {str(e)}")
            raise

    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """插入多个文档"""
        try:
            for document in documents:
                if 'createdTime' not in document:
                    document['createdTime'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            with self.get_collection(collection_name) as collection:
                result = collection.insert_many(documents)
                return [str(id) for id in result.inserted_ids]
        except Exception as e:
            logger.error(f"批量插入文档失败: {str(e)}")
            raise

    def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找单个文档"""
        try:
            with self.get_collection(collection_name) as collection:
                return collection.find_one(query)
        except Exception as e:
            logger.error(f"查找文档失败: {str(e)}")
            raise

    def find_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """查找多个文档"""
        try:
            with self.get_collection(collection_name) as collection:
                cursor = collection.find(query).skip(skip).limit(limit)
                if sort:
                    cursor = cursor.sort(sort)
                return list(cursor)
        except Exception as e:
            logger.error(f"查找多个文档失败: {str(e)}")
            raise

    def update_one(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """更新单个文档"""
        try:
            with self.get_collection(collection_name) as collection:
                result = collection.update_one(query, {"$set": update})
                return result.modified_count
        except Exception as e:
            logger.error(f"更新文档失败: {str(e)}")
            raise

    def update_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """更新多个文档"""
        try:
            with self.get_collection(collection_name) as collection:
                result = collection.update_many(query, {"$set": update})
                return result.modified_count
        except Exception as e:
            logger.error(f"批量更新文档失败: {str(e)}")
            raise

    def delete_one(self, collection_name: str, query: Dict[str, Any]) -> int:
        """删除单个文档"""
        try:
            with self.get_collection(collection_name) as collection:
                result = collection.delete_one(query)
                return result.deleted_count
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            raise

    def delete_many(self, collection_name: str, query: Dict[str, Any]) -> int:
        """删除多个文档"""
        try:
            with self.get_collection(collection_name) as collection:
                result = collection.delete_many(query)
                return result.deleted_count
        except Exception as e:
            logger.error(f"批量删除文档失败: {str(e)}")
            raise

    def count_documents(self, collection_name: str, query: Dict[str, Any]) -> int:
        """统计文档数量"""
        try:
            with self.get_collection(collection_name) as collection:
                return collection.count_documents(query)
        except Exception as e:
            logger.error(f"统计文档数量失败: {str(e)}")
            raise

    def aggregate(
        self,
        collection_name: str,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """聚合查询"""
        try:
            with self.get_collection(collection_name) as collection:
                return list(collection.aggregate(pipeline))
        except Exception as e:
            logger.error(f"聚合查询失败: {str(e)}")
            raise

    def create_index(
        self,
        collection_name: str,
        keys: List[tuple],
        unique: bool = False
    ):
        """创建索引"""
        try:
            with self.get_collection(collection_name) as collection:
                collection.create_index(keys, unique=unique)
        except Exception as e:
            logger.error(f"创建索引失败: {str(e)}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB 连接已关闭")

    def find_one_and_delete(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找并删除单个文档"""
        try:
            with self.get_collection(collection_name) as collection:
                return collection.find_one_and_delete(query)
        except Exception as e:
            logger.error(f"查找并删除文档失败: {str(e)}")
            raise

    def find_one_and_update(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        return_document: bool = False
    ) -> Optional[Dict[str, Any]]:
        """查找并更新单个文档"""
        try:
            with self.get_collection(collection_name) as collection:
                return collection.find_one_and_update(
                    query,
                    {"$set": update},
                    return_document=ReturnDocument.AFTER if return_document else ReturnDocument.BEFORE
                )
        except Exception as e:
            logger.error(f"查找并更新文档失败: {str(e)}")
            raise

# 示例请求:
# GET http://localhost:8000/?module_name=modules.database.mongoDB&method_name=insert_one&params={"cname":"test_collection","document":{"name": "张三", "age": 30, "email": "zhangsan@example.com"}}
#
# curl 示例:
# curl -X GET "http://localhost:8000/?module_name=modules.database.mongoDB&method_name=insert_one&params=%7B%22cname%22%3A%22test_collection%22%2C%22document%22%3A%7B%22name%22%3A%22%E5%BC%A0%E4%B8%89%22%2C%22age%22%3A30%2C%22email%22%3A%22zhangsan%40example.com%22%7D%7D"
#
# 参数说明:
# - cname: 集合名称
# - document: 要插入的文档
def insert_one(params: Dict[str, Any] = None) -> str:
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
    mongodb_instance = MongoDB()
    try:
        # 确保数据库已初始化
        mongodb_instance.initialize()

        doc_id = mongodb_instance.insert_one(
            cname,
            document
        )
        logger.info(f"插入文档ID: {doc_id}")
        return doc_id
    except Exception as e:
        logger.error(f"插入文档时出错: {e}")
        raise

# 示例请求:
# GET http://localhost:8000/?module_name=modules.database.mongoDB&method_name=find_one&params={"cname":"test_collection","query":{"name": "张三"}}
#
# curl 示例:
# curl -X GET "http://localhost:8000/?module_name=modules.database.mongoDB&method_name=find_one&params=%7B%22cname%22%3A%22test_collection%22%2C%22query%22%3A%7B%22name%22%3A%22%E5%BC%A0%E4%B8%89%22%7D"
#
# 参数说明:
# - cname: 集合名称
# - query: 查询条件
# - projection: 指定返回的字段（可选）
def find_one(params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
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
        mongodb_instance = MongoDB()
        mongodb_instance.initialize()

        document = mongodb_instance.find_one(
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

# 示例请求:
# GET http://localhost:8000/?module_name=modules.database.mongoDB&method_name=update_one&params={"cname":"test_collection","query":{"name": "张三"},"update":{"age": 31, "updated": true}}
#
# curl 示例:
# curl -X GET "http://localhost:8000/?module_name=modules.database.mongoDB&method_name=update_one&params=%7B%22cname%22%3A%22test_collection%22%2C%22query%22%3A%7B%22name%22%3A%22%E5%BC%A0%E4%B8%89%22%7D%2C%22update%22%3A%7B%22age%22%3A31%2C%22updated%22%3Atrue%7D"
#
# 参数说明:
# - cname: 集合名称
# - query: 查询条件
# - update: 更新内容
def update_one(params: Dict[str, Any] = None) -> int:
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

    mongodb_instance = MongoDB()
    try:
        # 确保数据库已初始化
        mongodb_instance.initialize()

        modified_count = mongodb_instance.update_one(
            cname,
            query,
            update
        )
        logger.info(f"更新的文档数: {modified_count}")
        return modified_count
    except Exception as e:
        logger.error(f"更新文档时出错: {e}")
        raise

# 示例请求:
# GET http://localhost:8000/?module_name=modules.database.mongoDB&method_name=find_one_and_update&params={"cname":"test_collection","query":{"name": "张三"},"update":{"status": "active"},"return_document": true}
#
# curl 示例:
# curl -X GET "http://localhost:8000/?module_name=modules.database.mongoDB&method_name=find_one_and_update&params=%7B%22cname%22%3A%22test_collection%22%2C%22query%22%3A%7B%22name%22%3A%22%E5%BC%A0%E4%B8%89%22%7D%2C%22update%22%3A%7B%22status%22%3A%22active%22%7D%2C%22return_document%22%3Atrue%7D"
#
# 参数说明:
# - cname: 集合名称
# - query: 查询条件
# - update: 更新内容
# - return_document: 是否返回更新后的文档
def find_one_and_update(params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
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

    mongodb_instance = MongoDB()
    try:
        # 确保数据库已初始化
        mongodb_instance.initialize()

        updated_user = mongodb_instance.find_one_and_update(
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

# 示例请求:
# GET http://localhost:8000/?module_name=modules.database.mongoDB&method_name=insert_many&params={"cname":"test_collection","documents":[{"name":"李四","age":25,"email":"lisi@example.com"},{"name":"王五","age":35,"email":"wangwu@example.com"}]}
#
# curl 示例:
# curl -X GET "http://localhost:8000/?module_name=modules.database.mongoDB&method_name=insert_many&params=%7B%22cname%22%3A%22test_collection%22%2C%22documents%22%3A%5B%7B%22name%22%3A%22%E6%9D%8E%E5%9B%9B%22%2C%22age%22%3A25%2C%22email%22%3A%22lisi%40example.com%22%7D%2C%7B%22name%22%3A%22%E7%8E%8B%E4%BA%94%22%2C%22age%22%3A35%2C%22email%22%3A%22wangwu%40example.com%22%7D%5D%7D"
#
# 参数说明:
# - cname: 集合名称
# - documents: 要插入的文档列表，每个文档是一个字典
def insert_many(params: Dict[str, Any] = None) -> List[str]:
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

    mongodb_instance = MongoDB()
    try:
        # 确保数据库已初始化
        mongodb_instance.initialize()

        batch_ids = mongodb_instance.insert_many(
            cname,
            documents
        )
        logger.info(f"批量插入ID: {batch_ids}")
        return batch_ids
    except Exception as e:
        logger.error(f"批量插入文档时出错: {e}")
        raise

# 示例请求:
# GET http://localhost:8000/?module_name=modules.database.mongoDB&method_name=find_many&params={"collection_name":"test_collection","filter_query":{"age":{"$gt":25}},"sort_criteria":[["age",-1]]}
#
# curl 示例:
# curl -X GET "http://localhost:8000/?module_name=modules.database.mongoDB&method_name=find_many&params=%7B%22collection_name%22%3A%22test_collection%22%2C%22filter_query%22%3A%7B%22age%22%3A%7B%22%24gt%22%3A25%7D%7D%2C%22sort_criteria%22%3A%5B%5B%22age%22%2C-1%5D%5D%7D"
#
# 参数说明:
# - collection_name: 集合名称
# - filter_query: 查询条件，支持MongoDB查询操作符
# - sort_criteria: 排序条件，格式为[["字段名", 1/-1]]，1表示升序，-1表示降序
def find_many(params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """查询多个文档

    Args:
        params: 参数字典，可包含：
            - collection_name: 集合名称，默认为"test_collection"
            - filter_query: 查询条件，默认查询年龄大于25的文档
            - sort_criteria: 排序条件，默认按年龄降序排列

    Returns:
        List[Dict[str, Any]]: 查询到的文档列表
    """
    if params is None:
        params = {}

    collection_name = params.get("collection_name", "test_collection")
    filter_query = params.get("filter_query", {"age": {"$gt": 25}})
    sort_criteria = params.get("sort_criteria", [["age", -1]])

    # 将列表格式的排序条件转换为元组格式
    sort_criteria = [tuple(criteria) for criteria in sort_criteria]

    db_instance = MongoDB()
    try:
        # 确保数据库已初始化
        db_instance.initialize()

        documents = db_instance.find_many(
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
            logger.info(f"文档: {doc['name']}, 年龄: {doc['age']}")
        return documents
    except Exception as e:
        logger.error(f"查询多个文档时出错: {e}")
        raise

# 示例请求:
# GET http://localhost:8000/?module_name=modules.database.mongoDB&method_name=count_documents&params={"cname":"test_collection","query":{"age":{"$gt":25}}}
#
# curl 示例:
# curl -X GET "http://localhost:8000/?module_name=modules.database.mongoDB&method_name=count_documents&params=%7B%22cname%22%3A%22test_collection%22%2C%22query%22%3A%7B%22age%22%3A%7B%22%24gt%22%3A25%7D%7D"
#
# 参数说明:
# - cname: 集合名称
# - query: 查询条件，支持MongoDB查询操作符
def count_documents(params: Dict[str, Any] = None) -> int:
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

    mongodb_instance = MongoDB()
    try:
        # 确保数据库已初始化
        mongodb_instance.initialize()

        count = mongodb_instance.count_documents(cname, query)
        logger.info(f"总文档数: {count}")
        return count
    except Exception as e:
        logger.error(f"统计文档数量时出错: {e}")
        raise

# 示例请求:
# GET http://localhost:8000/?module_name=modules.database.mongoDB&method_name=delete_many&params={"cname":"test_collection","query":{"age":{"$gt":25}}}
#
# curl 示例:
# curl -X GET "http://localhost:8000/?module_name=modules.database.mongoDB&method_name=delete_many&params=%7B%22cname%22%3A%22test_collection%22%2C%22query%22%3A%7B%22age%22%3A%7B%22%24gt%22%3A25%7D%7D"
#
# 参数说明:
# - cname: 集合名称
# - query: 查询条件，支持MongoDB查询操作符
def delete_many(params: Dict[str, Any] = None) -> int:
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

    mongodb_instance = MongoDB()
    try:
        # 确保数据库已初始化
        mongodb_instance.initialize()

        deleted = mongodb_instance.delete_many(cname, query)
        logger.info(f"清理测试数据，删除了 {deleted} 条记录")
        return deleted
    except Exception as e:
        logger.error(f"删除多个文档时出错: {e}")
        raise

# 示例请求:
# GET http://localhost:8000/?module_name=modules.database.mongoDB&method_name=list_collections&params={}
#
# curl 示例:
# curl -X GET "http://localhost:8000/?module_name=modules.database.mongoDB&method_name=list_collections&params=%7B%7D"
def list_collections(params: Dict[str, Any] = None) -> List[str]:
    """获取数据库中的所有集合列表

    Args:
        params: 参数字典，可选

    Returns:
        List[str]: 集合名称列表
    """
    if params is None:
        params = {}

    mongodb_instance = MongoDB()
    try:
        # 确保数据库已初始化
        mongodb_instance.initialize()

        collections = mongodb_instance._db.list_collection_names()
        logger.info(f"获取到 {len(collections)} 个集合")
        return collections
    except Exception as e:
        logger.error(f"获取集合列表时出错: {e}")
        raise

async def main(params: Dict[str, Any] = None):
    """MongoDB类使用示例
    
    Args:
        params: 参数字典，可选
        
    Returns:
        Dict[str, Any]: 测试结果
    """
    logger.info("开始MongoDB测试...")
    
    try:
        # 执行各个测试函数
        # insert_one(params)
        document = find_one(params)
        # update_one(params)
        # find_one_and_update(params)
        # insert_many(params)
        # find_many(params)
        # count_documents(params)
        # delete_many(params)
        
        logger.info("MongoDB测试完成")
        return {"status": "success", "message": "MongoDB测试完成", "document": document}
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print("开始执行MongoDB测试...")
    
    mongodb = MongoDB()
    try:
        mongodb.initialize()
        import asyncio
        result = asyncio.run(main())
        print(f"MongoDB测试执行完成！结果: {result}")
    finally:
        # 确保关闭MongoDB连接
        mongodb.close()
