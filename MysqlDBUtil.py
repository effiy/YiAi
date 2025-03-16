import aiomysql # type: ignore
from typing import List, Dict, Any, Optional
import logging
from contextlib import asynccontextmanager
from config import settings

class MysqlDBUtil:
    _instance = None
    _pool = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self):
        """初始化连接池"""
        if not self._pool:
            self._pool = await aiomysql.create_pool(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                db=settings.MYSQL_DATABASE,
                charset=settings.MYSQL_CHARSET,
                maxsize=settings.MYSQL_POOL_SIZE,
                minsize=2,
                autocommit=True
            )
            logging.info("MySQL 连接池已初始化")

    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接"""
        if not self._pool:
            await self.initialize()
        async with self._pool.acquire() as conn:
            yield conn

    async def execute_query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        执行查询语句
        :param sql: SQL 查询语句
        :param params: 查询参数
        :return: 查询结果列表
        """
        async with self.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, params)
                return await cursor.fetchall()

    async def execute_one(self, sql: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """
        执行查询语句并返回单条结果
        :param sql: SQL 查询语句
        :param params: 查询参数
        :return: 单条查询结果
        """
        async with self.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, params)
                return await cursor.fetchone()

    async def execute_update(self, sql: str, params: tuple = None) -> int:
        """
        执行更新语句（INSERT/UPDATE/DELETE）
        :param sql: SQL 更新语句
        :param params: 更新参数
        :return: 影响的行数
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                return await cursor.execute(sql, params)

    async def batch_execute(self, sql: str, params_list: List[tuple]) -> int:
        """
        批量执行 SQL 语句
        :param sql: SQL 语句
        :param params_list: 参数列表
        :return: 影响的行数
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                return await cursor.executemany(sql, params_list)

    async def execute_transaction(self, sql_list: List[str], params_list: List[tuple]) -> bool:
        """
        执行事务
        :param sql_list: SQL 语句列表
        :param params_list: 参数列表
        :return: 事务是否成功
        """
        async with self.get_connection() as conn:
            try:
                await conn.begin()
                async with conn.cursor() as cursor:
                    for sql, params in zip(sql_list, params_list):
                        await cursor.execute(sql, params)
                await conn.commit()
                return True
            except Exception as e:
                await conn.rollback()
                logging.error(f"Transaction failed: {str(e)}")
                return False

    async def close(self):
        """关闭连接池"""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None