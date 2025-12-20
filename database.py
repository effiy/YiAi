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
        await self._ensure_rss_link_index()
        
        self._initialized = True  # 设置初始化标志
        logger.info("数据库连接已成功初始化")
    
    async def _ensure_rss_link_index(self):
        """确保 rss 集合的 link 字段有唯一索引"""
        try:
            collection = self.mongodb.db['rss']
            indexes = await collection.list_indexes().to_list(length=None)
            
            # 检查是否已有 link 的唯一索引
            existing_index = self._find_link_index(indexes)
            
            if existing_index:
                if existing_index.get('unique'):
                    logger.info("rss 集合的 link 唯一索引已存在")
                else:
                    # 如果存在非唯一索引，需要删除后重新创建
                    logger.warning("rss 集合存在 link 的非唯一索引，将删除后重新创建唯一索引")
                    await collection.drop_index(existing_index.get('name'))
                    await self._create_link_index(collection)
            else:
                await self._create_link_index(collection)
        except Exception as e:
            self._handle_index_creation_error(e)
    
    def _find_link_index(self, indexes):
        """查找 link 字段的索引"""
        for idx in indexes:
            index_keys = idx.get('key', {})
            
            # 处理字典格式的索引键
            if isinstance(index_keys, dict) and 'link' in index_keys:
                return idx
            
            # 处理列表格式的索引键
            if isinstance(index_keys, list):
                for key_item in index_keys:
                    if isinstance(key_item, (list, tuple)) and len(key_item) >= 1 and key_item[0] == 'link':
                        return idx
        return None
    
    async def _create_link_index(self, collection):
        """创建 link 字段的唯一索引"""
        await collection.create_index([('link', 1)], unique=True, background=True)
        logger.info("已为 rss 集合创建 link 字段的唯一索引")
    
    def _handle_index_creation_error(self, error: Exception):
        """处理索引创建错误"""
        error_msg = str(error).lower()
        if 'duplicate key' in error_msg or 'e11000' in error_msg:
            logger.error("无法创建 rss 集合的 link 唯一索引: 集合中存在重复的 link 值。请先清理重复数据。")
        elif 'already exists' in error_msg:
            logger.info("rss 集合的 link 唯一索引已存在")
        else:
            logger.warning(f"创建 rss 集合的 link 唯一索引时出现警告: {str(error)}")
    
    async def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'mongodb'):
            await self.mongodb.close()
        self._initialized = False  # 重置初始化标志
        logger.info("数据库连接已成功关闭")

# 创建全局数据库实例
db = Database()

