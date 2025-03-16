from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any, Optional
from database import db
import logging
from utils.common import ensure_initialized, is_valid_date, is_number, handle_error, create_response

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

def parse_list_query(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """解析请求中的listQuery参数"""
    listQuery = {}
    for key, value in query_params.items():
        if key.startswith('listQuery'):
            parts = key.split('[')
            parts = [part.replace(']', '') for part in parts if part]
            
            outer_key = parts[0]
            inner_key = parts[1] if len(parts) > 1 else None
            index = int(parts[2]) if len(parts) > 2 else None

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
    
    return listQuery.get('listQuery', {})

def build_filter_conditions(listQuery: Dict[str, Any]) -> Dict[str, str]:
    """构建SQL过滤条件"""
    filter = {}
    
    for key in listQuery:
        if isinstance(listQuery[key], list) and listQuery[key]:
            if isinstance(listQuery[key][0], str) and listQuery[key][0]:
                quoted_values = ["'" + str(x) + "'" for x in listQuery[key]]
                filter[key] = f"{key} IN ({','.join(quoted_values)})"
            
            if len(listQuery[key]) == 2:
                if is_valid_date(listQuery[key][0]) and is_valid_date(listQuery[key][1]):
                    filter[key] = f"{key} BETWEEN '{listQuery[key][0]}' AND '{listQuery[key][1]}'"
                elif None in listQuery[key]:
                    if is_number(listQuery[key][0]) or is_number(listQuery[key][1]):
                        min_val = 0 if not is_number(listQuery[key][0]) else listQuery[key][0]
                        max_val = 9223372036854775806 if not is_number(listQuery[key][1]) else listQuery[key][1]
                        filter[key] = f"{key} BETWEEN {min_val} AND {max_val}"
                elif is_number(listQuery[key][0]) and is_number(listQuery[key][1]):
                    filter[key] = f"{key} BETWEEN {listQuery[key][0]} AND {listQuery[key][1]}"
        
        elif isinstance(listQuery[key], str) and listQuery[key]:
            if ',' not in listQuery[key]:
                filter[key] = f"{key} = '{listQuery[key]}'"
            else:
                search_terms = listQuery[key].split(',')
                filter[key] = f"{key} REGEXP '{'|'.join(search_terms)}'"
        
        elif isinstance(listQuery[key], int):
            filter[key] = f"{key} = {listQuery[key]}"
    
    return filter

@router.get("/")
@ensure_initialized()
async def query(request: Request, sql: str, pageNum: Optional[int] = 1, pageSize: Optional[int] = 1000):
    """执行SQL查询并返回分页结果"""
    try:
        query_params = dict(request.query_params)
        listQuery = parse_list_query(query_params)
        sqlFilePath = f'sqls/{sql}.sql'
        
        params = {
            'limit': f"{(pageNum - 1) * pageSize},{pageSize}"
        }
        
        filter = build_filter_conditions(listQuery)
        params['listQuery'] = ' WHERE 1 = 1 ' + ''.join(f" AND {condition}" for condition in filter.values())
        
        sqlTable = await db.mysql.query_table(sqlFilePath, params)
        
        return create_response(
            code=200,
            message="查询成功",
            data={
                'data': [dict(zip(sqlTable['th'], td)) for td in sqlTable['tds']],
                'total': (await db.mysql.execute_query('SELECT FOUND_ROWS()'))[0]['FOUND_ROWS()']
            }
        )
    except Exception as e:
        return handle_error(e)

@router.get("/tables")
@ensure_initialized()
async def get_tables() -> Dict[str, Any]:
    """获取数据库中所有表名"""
    try:
        tables = await db.mysql.query("SHOW TABLES")
        return create_response(code=200, message="获取成功", data=tables)
    except Exception as e:
        return handle_error(e)

@router.get("/query")
@ensure_initialized()
async def execute_query(sql: str) -> Dict[str, Any]:
    """执行自定义查询语句"""
    if not sql.strip().lower().startswith("select"):
        return create_response(code=400, message="只允许SELECT查询")
    
    try:
        results = await db.mysql.execute_query(sql)
        return create_response(code=200, message="查询成功", data=results)
    except Exception as e:
        return handle_error(e, status_code=400)

@router.post("/execute")
@ensure_initialized()
async def execute_command(sql: str) -> Dict[str, Any]:
    """执行数据库修改命令"""
    if sql.strip().lower().startswith("select"):
        return create_response(code=400, message="请使用/query接口执行SELECT查询")
    
    try:
        affected_rows = await db.mysql.execute_update(sql)
        return create_response(
            code=200,
            message=f"成功影响{affected_rows}行",
            data={"affected_rows": affected_rows}
        )
    except Exception as e:
        return handle_error(e, status_code=400) 