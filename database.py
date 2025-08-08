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
