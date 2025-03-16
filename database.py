import logging
from typing import Optional

from MongoDBUtil import MongoDBUtil
from MysqlDBUtil import MysqlDBUtil

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
        self.mongodb = MongoDBUtil()
        
        # 初始化 MySQL 连接池
        self.mysql = MysqlDBUtil()
        
        await self.mysql.initialize()
        
        self._initialized = True
        logger.info("数据库连接初始化成功")
    
    async def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'mysql'):
            await self.mysql.close()
        if hasattr(self, 'mongodb'):
            await self.mongodb.close()
        logger.info("数据库连接已成功关闭")

# 创建全局数据库实例
db = Database()