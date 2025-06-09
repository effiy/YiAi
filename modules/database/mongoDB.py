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
        """插入单个文档
        
        示例:
        ```python
        mongodb = MongoDB()
        user_id = await mongodb.insert_one(
            "users", 
            {"name": "张三", "age": 30, "email": "zhangsan@example.com"}
        )
        ```
        """
        if 'createdTime' not in document:
            document['createdTime'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        result = await self._db[collection_name].insert_one(document)
        return str(result.inserted_id)

    async def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """插入多个文档
        
        示例:
        ```python
        mongodb = MongoDB()
        user_ids = await mongodb.insert_many(
            "users", 
            [
                {"name": "张三", "age": 30, "email": "zhangsan@example.com"},
                {"name": "李四", "age": 25, "email": "lisi@example.com"}
            ]
        )
        ```
        """
        for document in documents:
            if 'createdTime' not in document:
                document['createdTime'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        result = await self._db[collection_name].insert_many(documents)
        return [str(id) for id in result.inserted_ids]

    async def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找单个文档
        
        示例:
        ```python
        mongodb = MongoDB()
        user = await mongodb.find_one("users", {"name": "张三"})
        if user:
            print(f"找到用户: {user['name']}, 邮箱: {user['email']}")
        ```
        """
        return await self._db[collection_name].find_one(query)

    async def find_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """查找多个文档
        
        示例:
        ```python
        mongodb = MongoDB()
        # 查找年龄大于25的用户，按年龄降序排列，跳过前5个，最多返回10个
        users = await mongodb.find_many(
            "users", 
            {"age": {"$gt": 25}}, 
            skip=5, 
            limit=10, 
            sort=[("age", -1)]
        )
        for user in users:
            print(f"用户: {user['name']}, 年龄: {user['age']}")
        ```
        """
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
        """更新单个文档
        
        示例:
        ```python
        mongodb = MongoDB()
        # 更新张三的年龄
        modified_count = await mongodb.update_one(
            "users", 
            {"name": "张三"}, 
            {"age": 31}
        )
        print(f"更新的文档数: {modified_count}")
        ```
        """
        result = await self._db[collection_name].update_one(query, {"$set": update})
        return result.modified_count

    async def update_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """更新多个文档
        
        示例:
        ```python
        mongodb = MongoDB()
        # 将所有年龄小于18的用户标记为未成年
        modified_count = await mongodb.update_many(
            "users", 
            {"age": {"$lt": 18}}, 
            {"isAdult": False}
        )
        print(f"更新的文档数: {modified_count}")
        ```
        """
        result = await self._db[collection_name].update_many(query, {"$set": update})
        return result.modified_count

    async def delete_one(self, collection_name: str, query: Dict[str, Any]) -> int:
        """删除单个文档
        
        示例:
        ```python
        mongodb = MongoDB()
        # 删除名为张三的用户
        deleted_count = await mongodb.delete_one("users", {"name": "张三"})
        print(f"删除的文档数: {deleted_count}")
        ```
        """
        result = await self._db[collection_name].delete_one(query)
        return result.deleted_count

    async def delete_many(self, collection_name: str, query: Dict[str, Any]) -> int:
        """删除多个文档
        
        示例:
        ```python
        mongodb = MongoDB()
        # 删除所有未激活的用户
        deleted_count = await mongodb.delete_many("users", {"active": False})
        print(f"删除的文档数: {deleted_count}")
        ```
        """
        result = await self._db[collection_name].delete_many(query)
        return result.deleted_count

    async def count_documents(self, collection_name: str, query: Dict[str, Any]) -> int:
        """统计文档数量
        
        示例:
        ```python
        mongodb = MongoDB()
        # 统计年龄大于30的用户数量
        count = await mongodb.count_documents("users", {"age": {"$gt": 30}})
        print(f"符合条件的用户数: {count}")
        ```
        """
        return await self._db[collection_name].count_documents(query)

    async def aggregate(
        self,
        collection_name: str,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """聚合查询
        
        示例:
        ```python
        mongodb = MongoDB()
        # 按年龄段统计用户数量
        pipeline = [
            {"$group": {"_id": {"$floor": {"$divide": ["$age", 10]}}, "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        results = await mongodb.aggregate("users", pipeline)
        for result in results:
            age_group = f"{result['_id']*10}-{result['_id']*10+9}"
            print(f"年龄段 {age_group}: {result['count']} 人")
        ```
        
        # 按部门统计员工平均薪资
        pipeline = [
            {"$group": {"_id": "$department", "avg_salary": {"$avg": "$salary"}}},
            {"$sort": {"avg_salary": -1}}
        ]
        results = await mongodb.aggregate("employees", pipeline)
        for result in results:
            print(f"部门: {result['_id']}, 平均薪资: {result['avg_salary']}")
        ```
        """
        return await self._db[collection_name].aggregate(pipeline).to_list(None)

    def get_collection(self, collection_name: str):
        """获取集合对象
        
        示例:
        ```python
        mongodb = MongoDB()
        users_collection = mongodb.get_collection("users")
        # 现在可以直接使用users_collection进行更复杂的操作
        
        # 例如，执行findAndModify操作
        from pymongo import ReturnDocument
        result = await users_collection.find_one_and_update(
            {"_id": user_id},
            {"$inc": {"login_count": 1}},
            return_document=ReturnDocument.AFTER
        )
        ```
        """
        return self._db[collection_name]

    async def create_index(
        self,
        collection_name: str,
        keys: List[tuple],
        unique: bool = False
    ):
        """创建索引
        
        示例:
        ```python
        mongodb = MongoDB()
        # 在users集合上创建email字段的唯一索引
        await mongodb.create_index("users", [("email", 1)], unique=True)
        # 在products集合上创建复合索引
        await mongodb.create_index("products", [("category", 1), ("price", -1)])
        
        # 创建TTL索引，自动删除过期文档
        await mongodb.create_index("sessions", [("last_activity", 1)], 
                                  expireAfterSeconds=3600)  # 1小时后过期
        ```
        """
        await self._db[collection_name].create_index(keys, unique=unique)

    async def close(self):
        """关闭数据库连接
        
        示例:
        ```python
        mongodb = MongoDB()
        # 数据库操作完成后关闭连接
        await mongodb.close()
        
        # 在应用程序退出前关闭
        async def shutdown_event():
            mongodb = MongoDB()
            await mongodb.close()
            print("数据库连接已安全关闭")
        ```
        """
        if self._client:
            self._client.close()
            logger.info("MongoDB 连接已关闭")

    async def find_one_and_delete(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找并删除单个文档
        
        示例:
        ```python
        mongodb = MongoDB()
        # 查找并删除最老的过期任务
        expired_task = await mongodb.find_one_and_delete(
            "tasks", 
            {"status": "expired", "createdTime": {"$lt": "2023-01-01"}}
        )
        if expired_task:
            print(f"已删除过期任务: {expired_task['name']}")
            
        # 删除并返回购物车中的第一个商品
        removed_item = await mongodb.find_one_and_delete(
            "shopping_cart",
            {"user_id": user_id},
            sort=[("added_time", 1)]  # 按添加时间升序，删除最早添加的
        )
        ```
        """
        result = await self._db[collection_name].find_one_and_delete(query)
        return result

    async def find_one_and_update(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        return_document: bool = False
    ) -> Optional[Dict[str, Any]]:
        """查找并更新单个文档
        
        示例:
        ```python
        mongodb = MongoDB()
        # 查找名为"张三"的用户并将其状态更新为"active"，返回更新后的文档
        updated_user = await mongodb.find_one_and_update(
            "users",
            {"name": "张三"},
            {"status": "active", "lastLogin": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')},
            return_document=True
        )
        if updated_user:
            print(f"用户 {updated_user['name']} 状态已更新为: {updated_user['status']}")
            
        # 查找商品并减少库存，同时确保库存不会变为负数
        updated_product = await mongodb.find_one_and_update(
            "products",
            {"_id": product_id, "stock": {"$gte": quantity}},
            {"$inc": {"stock": -quantity}},
            return_document=True
        )
        if updated_product:
            print(f"商品 {updated_product['name']} 库存更新为: {updated_product['stock']}")
        else:
            print("库存不足，无法完成操作")
        ```
        """
        result = await self._db[collection_name].find_one_and_update(
            query,
            {"$set": update},
            return_document=ReturnDocument.AFTER if return_document else ReturnDocument.BEFORE
        )
        return result

# 主函数，用于测试和演示MongoDB类的使用
async def main():
    """MongoDB类使用示例"""
    try:
        # 初始化MongoDB连接
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
    finally:
        # 关闭连接
        await mongodb.close()

# 如果直接运行此模块，则执行main函数
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())