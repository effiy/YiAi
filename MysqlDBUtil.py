import pymysql
from pymysql.cursors import DictCursor
from dbutils.pooled_db import PooledDB
from typing import List, Dict, Any, Optional, Union
import logging

class MysqlDBUtil:
    _instance = None
    _pool = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, host: str = "localhost", 
                 port: int = 3306,
                 user: str = "root",
                 password: str = "",
                 database: str = "",
                 charset: str = "utf8mb4",
                 pool_size: int = 5):
        if not self._pool:
            self._pool = PooledDB(
                creator=pymysql,
                maxconnections=pool_size,
                mincached=2,
                maxcached=5,
                blocking=True,
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                charset=charset,
                cursorclass=DictCursor
            )
            logging.info("MySQL connection pool initialized")

    def get_connection(self):
        """获取数据库连接"""
        return self._pool.connection()

    def execute_query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        执行查询语句
        :param sql: SQL 查询语句
        :param params: 查询参数
        :return: 查询结果列表
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchall()

    def execute_one(self, sql: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """
        执行查询语句并返回单条结果
        :param sql: SQL 查询语句
        :param params: 查询参数
        :return: 单条查询结果
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchone()

    def execute_update(self, sql: str, params: tuple = None) -> int:
        """
        执行更新语句（INSERT/UPDATE/DELETE）
        :param sql: SQL 更新语句
        :param params: 更新参数
        :return: 影响的行数
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                rows = cursor.execute(sql, params)
                conn.commit()
                return rows

    def batch_execute(self, sql: str, params_list: List[tuple]) -> int:
        """
        批量执行 SQL 语句
        :param sql: SQL 语句
        :param params_list: 参数列表
        :return: 影响的行数
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                rows = cursor.executemany(sql, params_list)
                conn.commit()
                return rows

    def execute_transaction(self, sql_list: List[str], params_list: List[tuple]) -> bool:
        """
        执行事务
        :param sql_list: SQL 语句列表
        :param params_list: 参数列表
        :return: 事务是否成功
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                for sql, params in zip(sql_list, params_list):
                    cursor.execute(sql, params)
                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Transaction failed: {str(e)}")
            return False
        finally:
            conn.close()