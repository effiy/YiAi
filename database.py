import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient

from modules.database.mongoClient import MongoClient

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    _instance: Optional['Database'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    async def initialize(self):
        """异步初始化数据库连接"""
        if self._initialized:
            return
            
        # 初始化 MongoDB
        self.mongodb = MongoClient()
        await self.mongodb.initialize()  # 确保 MongoDB 客户端已初始化
        
        # 为 rss 集合创建 link 字段的唯一索引
        try:
            collection = self.mongodb.db['rss']
            # 检查索引是否已存在
            indexes = await collection.list_indexes().to_list(length=None)
            index_names = [idx.get('name') for idx in indexes]
            
            # 检查是否已有 link 的唯一索引
            link_index_exists = False
            for idx in indexes:
                # MongoDB 索引的 key 是列表，格式如 [('link', 1)]
                index_keys = idx.get('key', {})
                # 检查是否是 link 字段的索引
                if isinstance(index_keys, dict) and 'link' in index_keys:
                    link_index_exists = True
                    if idx.get('unique'):
                        logger.info("rss 集合的 link 唯一索引已存在")
                    else:
                        # 如果存在非唯一索引，需要删除后重新创建
                        logger.warning("rss 集合存在 link 的非唯一索引，将删除后重新创建唯一索引")
                        await collection.drop_index(idx.get('name'))
                        link_index_exists = False
                    break
                elif isinstance(index_keys, list):
                    # 处理列表格式的索引键
                    for key_item in index_keys:
                        if isinstance(key_item, (list, tuple)) and len(key_item) >= 1 and key_item[0] == 'link':
                            link_index_exists = True
                            if idx.get('unique'):
                                logger.info("rss 集合的 link 唯一索引已存在")
                            else:
                                # 如果存在非唯一索引，需要删除后重新创建
                                logger.warning("rss 集合存在 link 的非唯一索引，将删除后重新创建唯一索引")
                                await collection.drop_index(idx.get('name'))
                                link_index_exists = False
                            break
                    if link_index_exists:
                        break
            
            if not link_index_exists:
                # 创建唯一索引
                await collection.create_index([('link', 1)], unique=True, background=True)
                logger.info("已为 rss 集合创建 link 字段的唯一索引")
        except Exception as e:
            error_msg = str(e).lower()
            # 如果是因为数据中存在重复的 link 值导致无法创建唯一索引
            if 'duplicate key' in error_msg or 'e11000' in error_msg:
                logger.error(f"无法创建 rss 集合的 link 唯一索引: 集合中存在重复的 link 值。请先清理重复数据。")
            elif 'already exists' in error_msg:
                logger.info("rss 集合的 link 唯一索引已存在")
            else:
                logger.warning(f"创建 rss 集合的 link 唯一索引时出现警告: {str(e)}")
        
        self._initialized = True  # 设置初始化标志
        logger.info("数据库连接已成功初始化")
    
    async def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'mongodb'):
            await self.mongodb.close()
        self._initialized = False  # 重置初始化标志
        logger.info("数据库连接已成功关闭")

# 创建全局数据库实例
db = Database()

