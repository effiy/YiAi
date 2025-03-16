from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Dict, Any, Optional
from database import db
import logging
from functools import wraps
from datetime import datetime

# 创建路由器，设置前缀和标签
router = APIRouter(
    prefix="/mysql",
    tags=["mysql"],
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad Request"},
        500: {"description": "Internal Server Error"}
    },
)

# 配置日志记录器
logger = logging.getLogger(__name__)

def ensure_initialized():
    """确保数据库已初始化的装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 检查数据库是否已初始化
            if not hasattr(db, '_initialized') or not db._initialized:
                logger.info("Initializing database connection")
                await db.initialize()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def is_valid_date(date_str):
    """检查字符串是否为有效日期格式"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False

def is_number(value):
    """检查值是否为数字"""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

def parse_list_query(query_params):
    """解析请求中的listQuery参数"""
    listQuery = {}
    for key, value in query_params.items():
        if key.startswith('listQuery'):
            # 解析 listQuery 参数，格式为 listQuery[key][index] 的样式
            parts = key.split('[')
            parts = [part.replace(']', '') for part in parts if part]
            
            # 获取 key 和嵌套的 index
            outer_key = parts[0]
            inner_key = parts[1] if len(parts) > 1 else None
            index = int(parts[2]) if len(parts) > 2 else None

            # 处理嵌套结构
            if outer_key not in listQuery:
                listQuery[outer_key] = {}
            
            if inner_key:
                if index is not None:
                    if inner_key not in listQuery[outer_key]:
                        listQuery[outer_key][inner_key] = []
                    listQuery[outer_key][inner_key].append(value)
                else:
                    listQuery[outer_key][inner_key] = value
            else:
                listQuery[outer_key] = value
    
    # 如果存在listQuery键，则取其值
    if 'listQuery' in listQuery:
        listQuery = listQuery['listQuery']
    
    return listQuery

def build_filter_conditions(listQuery):
    """构建SQL过滤条件"""
    filter = {}
    
    for key in listQuery:
        # 处理列表类型的查询条件
        if isinstance(listQuery[key], list) and len(listQuery[key]) > 0:
            # 处理字符串列表，构建IN条件
            if isinstance(listQuery[key][0], str) and len(listQuery[key][0]) > 0:
                quoted_values = ["'" + str(x) + "'" for x in listQuery[key]]
                filter[key] = f"{key} IN ({','.join(quoted_values)})"
            
            # 处理长度为2的列表（范围查询）
            if len(listQuery[key]) == 2:
                # 日期范围查询
                if is_valid_date(listQuery[key][0]) and is_valid_date(listQuery[key][1]):
                    filter[key] = {
                        '$gte': listQuery[key][0],
                        '$lt': listQuery[key][1]
                    }
                # 处理包含None的数值范围
                if None in listQuery[key]:
                    if is_number(listQuery[key][0]) or is_number(listQuery[key][1]):
                        min_val = 0 if not is_number(listQuery[key][0]) else listQuery[key][0]
                        max_val = 9223372036854775806 if not is_number(listQuery[key][1]) else listQuery[key][1]
                        filter[key] = f"{key} <= {max_val} AND {key} >= {min_val}"
                # 数值范围查询
                elif is_number(listQuery[key][0]) and is_number(listQuery[key][1]):
                    filter[key] = f"{key} <= {listQuery[key][1]} AND {key} >= {listQuery[key][0]}"
        
        # 处理单个字符串查询条件
        elif isinstance(listQuery[key], str) and len(listQuery[key]) > 0:
            if ',' not in listQuery[key]:
                filter[key] = f"{key} = '{listQuery[key]}'"
            else:
                # 处理包含逗号的字符串（多值查询）
                searchStrAry = listQuery[key].split(',')
                filter[key] = f"{key} REGEXP '{'|'.join(searchStrAry)}'"
        
        # 处理整数查询条件
        elif isinstance(listQuery[key], int):
            filter[key] = {'$eq': listQuery[key]}
    
    return filter

@router.get("/")
@ensure_initialized()
async def query(request: Request, sql: str, pageNum: Optional[int] = 1, pageSize: Optional[int] = 1000):
    """
    执行SQL查询并返回分页结果
    
    Args:
        request (Request): 请求对象，包含查询参数
        sql (str): SQL文件名（不含扩展名）
        pageNum (int): 页码，默认为1
        pageSize (int): 每页记录数，默认为1000
    
    Returns:
        Dict: 包含查询结果和总记录数的字典
    """
    try:
        # 获取查询参数并解析
        query_params = dict(request.query_params)
        listQuery = parse_list_query(query_params)
        
        # 构建SQL文件路径
        sqlFilePath = f'sqls/{sql}.sql'
        
        # 初始化参数字典
        params = {
            'limit': f"{(pageNum - 1) * pageSize},{pageSize}"
        }
        
        # 构建过滤条件
        filter = build_filter_conditions(listQuery)
        
        # 构建WHERE子句
        params['listQuery'] = ' WHERE 1 = 1 '
        for key in filter:
            if isinstance(filter[key], dict):
                # 处理MongoDB风格的查询条件
                if '$eq' in filter[key]:
                    params['listQuery'] += f" AND {key} = {filter[key]['$eq']} "
                elif '$gte' in filter[key] and '$lt' in filter[key]:
                    params['listQuery'] += f" AND {key} >= '{filter[key]['$gte']}' AND {key} < '{filter[key]['$lt']}' "
            else:
                params['listQuery'] += f" AND {filter[key]} "
        
        # 执行查询
        sqlTable = await db.mysql.query_table(sqlFilePath, params)
        
        # 处理查询结果
        res = {
            'data': [dict(zip(sqlTable['th'], td)) for td in sqlTable['tds']],
            'total': (await db.mysql.execute_query('SELECT FOUND_ROWS()'))[0]['FOUND_ROWS()']
        }
        
        return res
    except Exception as e:
        # 记录错误并抛出异常
        logger.error(f"查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询错误: {str(e)}")

@router.get("/tables", response_model=List[str])
@ensure_initialized()
async def get_tables() -> List[str]:
    """
    获取数据库中所有表名
    
    Returns:
        List[str]: 数据库中所有表的名称列表
    
    Raises:
        HTTPException: 当数据库操作失败时抛出
    """
    try:
        # 执行SHOW TABLES查询
        tables = await db.mysql.query("SHOW TABLES")
        logger.debug(f"Retrieved {len(tables)} tables from database")
        return tables
    except Exception as e:
        # 记录错误并抛出异常
        logger.error(f"Failed to get tables: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/query", response_model=List[Dict[str, Any]])
@ensure_initialized()
async def execute_query(sql: str) -> List[Dict[str, Any]]:
    """
    执行自定义查询语句
    
    Args:
        sql (str): 要执行的SQL查询语句
    
    Returns:
        List[Dict[str, Any]]: 查询结果列表
    
    Raises:
        HTTPException: 当查询语句无效或执行失败时抛出
    """
    # 安全检查：只允许SELECT查询
    if not sql.strip().lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
    
    try:
        # 执行查询
        results = await db.mysql.execute_query(sql)
        logger.debug(f"Executed query: {sql[:100]}...")
        return results
    except Exception as e:
        # 记录错误并抛出异常
        logger.error(f"Query execution failed: {str(e)}, SQL: {sql}")
        raise HTTPException(status_code=400, detail=f"Query error: {str(e)}")

@router.post("/execute", response_model=Dict[str, Any])
@ensure_initialized()
async def execute_command(sql: str) -> Dict[str, Any]:
    """
    执行数据库修改命令（INSERT/UPDATE/DELETE等）
    
    Args:
        sql (str): 要执行的SQL命令
    
    Returns:
        Dict[str, Any]: 包含受影响行数和执行状态的字典
    
    Raises:
        HTTPException: 当命令执行失败时抛出
    """
    # 安全检查：不允许SELECT查询
    if sql.strip().lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Use /query endpoint for SELECT queries")
    
    try:
        # 执行更新命令
        affected_rows = await db.mysql.execute_update(sql)
        logger.info(f"Successfully executed command affecting {affected_rows} rows")
        return {
            "affected_rows": affected_rows,
            "status": "success",
            "message": f"Successfully affected {affected_rows} rows"
        }
    except Exception as e:
        # 记录错误并抛出异常
        logger.error(f"Command execution failed: {str(e)}, SQL: {sql}")
        raise HTTPException(status_code=400, detail=f"Execution error: {str(e)}") 