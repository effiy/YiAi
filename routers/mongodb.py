from fastapi import APIRouter, Request
from typing import Optional, Dict, Any, List
import re
from datetime import datetime
import uuid
import logging
from database import db
from Resp import ok as Resp_ok
from functools import wraps

router = APIRouter(
    prefix="/mongodb",
    tags=["mongodb"],
    responses={404: {"description": "Not found"}},
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

def is_valid_date(date_str: str) -> bool:
    """检查字符串是否为有效日期格式"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False

def is_number(value: Any) -> bool:
    """检查值是否为数字"""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

def build_filter(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """构建MongoDB查询过滤器"""
    filter_dict = {}
    
    for key, value in query_params.items():
        # 处理列表类型的查询参数
        if isinstance(value, list) and value:
            # 如果列表不为空且第一个元素不为空，使用$in操作符
            if value[0]:
                filter_dict[key] = {'$in': value}
                
            # 处理长度为2的数组（范围查询）
            if len(value) == 2:
                # 日期范围查询
                if is_valid_date(value[0]) and is_valid_date(value[1]):
                    filter_dict[key] = {'$gte': value[0], '$lt': value[1]}
                
                # 处理包含None的数字范围查询
                elif None in value and (is_number(value[0]) or is_number(value[1])):
                    start = 0 if not is_number(value[0]) else value[0]
                    end = 9223372036854775806 if not is_number(value[1]) else value[1]
                    filter_dict[key] = {'$gte': start, '$lt': end}
                
                # 数字范围查询
                elif is_number(value[0]) and is_number(value[1]):
                    filter_dict[key] = {'$gte': value[0], '$lt': value[1]}
        
        # 处理字符串模糊查询
        elif isinstance(value, str) and value and ',' not in value:
            filter_dict[key] = re.compile('.*' + value + '.*')
        
        # 处理整数精确匹配
        elif isinstance(value, int):
            filter_dict[key] = {'$eq': value}
        
        # 处理逗号分隔的多条件OR查询
        elif isinstance(value, str) and value and ',' in value:
            search_terms = value.split(',')
            search_conditions = [{key: re.compile('.*' + term + '.*')} for term in search_terms]
            filter_dict['$or'] = search_conditions
    
    return filter_dict

@router.get("/")
@ensure_initialized()
async def query(request: Request):
    """
    查询MongoDB集合中的数据
    
    参数:
    - cname: 集合名称
    - pageNum: 页码
    - pageSize: 每页数量
    - sort: 排序字段，格式为 "field:order"，例如 "createdTime:-1"
    - 其他参数: 作为查询条件
    
    返回:
    - 分页后的数据列表和总数
    """
    # 获取查询参数
    query_params = dict(request.query_params)
    
    # 提取基本参数
    cname = query_params.pop('cname')
    page_num = int(query_params.pop('pageNum'))
    page_size = int(query_params.pop('pageSize'))
    
    # 处理排序参数
    sort_param = query_params.pop('sort', 'createdTime:-1')
    sort_field, sort_order = sort_param.split(':') if ':' in sort_param else (sort_param, '-1')
    sort_order = int(sort_order)
    
    # 构建过滤条件
    filter_dict = build_filter(query_params)
    
    # 设置要返回的字段（排除_id字段）
    projection = {'_id': 0}
    
    # 执行查询，并进行分页
    collection = db.mongodb.db[cname]
    cursor = collection.find(filter_dict, projection) \
        .sort(sort_field, sort_order) \
        .skip((page_num - 1) * page_size) \
        .limit(page_size)
    
    # 获取数据和总数
    data = await cursor.to_list(length=page_size)
    total = await collection.count_documents(filter_dict)
    
    # 返回结果
    return Resp_ok(
        data={
            'list': data,
            'total': total
        }
    )

@router.post("/")
@ensure_initialized()
async def update(post_data: Optional[Dict[str, Any]] = {}):
    """
    更新或插入MongoDB集合中的数据
    
    参数:
    - post_data: 包含cname(集合名)和其他数据字段的字典
    
    返回:
    - 更新或插入的文档key
    """
    cname = post_data.pop('cname')
    collection = db.mongodb.db[cname]
    
    # 根据不同情况处理数据
    if 'key' in post_data and post_data['key']:
        # 修改现有文档
        filter_dict = {'key': post_data['key']}
        await collection.find_one_and_update(filter_dict, {"$set": post_data})
    
    elif 'filter' in post_data and post_data['filter']:
        # 使用自定义过滤器查找并更新
        filter_dict = post_data['filter']
        cursor = collection.find(filter_dict).sort("createdTime", -1)
        document = await cursor.to_list(length=1)
        
        if document:
            # 如果找到匹配的文档，则更新
            await collection.find_one_and_update(filter_dict, {"$set": post_data})
        else:
            # 如果没有找到匹配的文档，则新增
            post_data['key'] = str(uuid.uuid4())
            await collection.insert_one(post_data)
    
    else:
        # 没有指定key或filter，直接新增文档
        post_data['key'] = str(uuid.uuid4())
        await collection.insert_one(post_data)
    
    return Resp_ok(data=post_data['key'])

@router.delete("/")
@ensure_initialized()
async def delete(cname: Optional[str] = '', key: Optional[str] = ''):
    """
    删除MongoDB集合中的数据
    
    参数:
    - cname: 集合名称
    - key: 要删除的文档的key
    
    返回:
    - 成功响应
    """
    collection = db.mongodb.db[cname]
    filter_dict = {'key': key}
    await collection.delete_many(filter_dict)
    return Resp_ok()