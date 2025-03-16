import aiomysql # type: ignore
from typing import List, Dict, Any, Optional
import logging, datetime
from contextlib import asynccontextmanager
from config import settings

def datetime_handler(x):
    """
    处理日期时间对象，将其转换为ISO格式字符串
    :param x: 输入对象
    :return: 如果是datetime对象则返回ISO格式字符串，否则返回原对象
    """
    return x.isoformat() if isinstance(x, datetime.datetime) else x

def NewSql(sqlFilePath, params={}, isGet=False):
    """
    从SQL文件中读取SQL语句并替换参数
    :param sqlFilePath: SQL文件路径
    :param params: 替换参数字典
    :param isGet: 是否为获取单条记录的查询
    :return: 处理后的SQL语句
    """
    limitSql = ' limit 1' if isGet else ' '
    with open(sqlFilePath, 'r', encoding='utf-8') as f:
        newSql = ' '.join(line.strip() for line in f) + limitSql
    for key, value in params.items():
        replaceHold = '{ ' + key + ' }'
        newSql = newSql.replace(replaceHold, value)
    return newSql
class MysqlDBUtil:
    """MySQL数据库工具类，提供数据库连接池和各种数据库操作方法"""
    _instance = None  # 单例实例
    _pool = None      # 连接池

    def __new__(cls, *args, **kwargs):
        """
        实现单例模式
        :return: 类的唯一实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self):
        """初始化数据库连接池"""
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
    
    async def query(self, query, *parameters, **kwparameters):
        """
        返回给定查询和参数的行列表
        :param query: SQL查询语句
        :param parameters: 位置参数
        :param kwparameters: 关键字参数
        :return: 查询结果行列表
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, parameters or kwparameters)
                return await cursor.fetchall()

    async def get(self, query, *parameters, **kwparameters):
        """
        获取单条查询结果
        :param query: SQL查询语句
        :param parameters: 位置参数
        :param kwparameters: 关键字参数
        :return: 单条查询结果或None
        :raises: Exception 当查询返回多条结果时
        """
        rows = await self.query(query, *parameters, **kwparameters)
        if not rows:
            return None
        if len(rows) > 1:
            raise Exception("Multiple rows returned for Database.get() query")
        return rows[0]

    async def table(self, query, *parameters, **kwparameters):
        """
        将查询结果格式化为表格形式
        :param query: SQL查询语句
        :param parameters: 位置参数
        :param kwparameters: 关键字参数
        :return: 包含表头和数据的字典
        """
        table = { 'th': [], 'tds': [] }
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, parameters or kwparameters)
                table['th'] = [d[0] for d in cursor.description]
                itemsAry = await cursor.fetchall()
                table['tds'] = []
                for itemAry in itemsAry:
                    td = []
                    for item in itemAry:
                        td.append(datetime_handler(item))
                    table['tds'].append(td)
        return table

    async def query_table(self, sqlFilePath, params={}, isGet=False):
        """
        从SQL文件读取查询并返回表格形式的结果
        :param sqlFilePath: SQL文件路径
        :param params: 替换参数
        :param isGet: 是否为获取单条记录的查询
        :return: 表格形式的查询结果
        """
        querySql = NewSql(sqlFilePath, params, isGet)
        return await self.table(querySql)

    async def query_file(self, sqlFilePath, params={}, isGet=False):
        """
        从SQL文件读取查询并执行
        :param sqlFilePath: SQL文件路径
        :param params: 替换参数
        :param isGet: 是否为获取单条记录的查询
        :return: 查询结果行列表
        """
        querySql = NewSql(sqlFilePath, params, isGet)
        return await self.query(querySql)

    @asynccontextmanager
    async def get_connection(self):
        """
        获取数据库连接的异步上下文管理器
        :yield: 数据库连接
        """
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
        """
        关闭连接池
        """
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None