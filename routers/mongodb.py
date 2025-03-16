from fastapi import APIRouter, Request
from typing import Optional, Dict, Any, List
import re
from datetime import datetime
import uuid
from database import db
from Resp import Resp


router = APIRouter(
    prefix="/mongodb",
    tags=["mongodb"],
    responses={404: {"description": "Not found"}},
)

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
def query(request: Request):
    """
    查询MongoDB集合中的数据
    
    参数:
    - cname: 集合名称
    - pageNum: 页码
    - pageSize: 每页数量
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
    
    # 构建过滤条件
    filter_dict = build_filter(query_params)
    
    # 设置要返回的字段（排除_id字段）
    projection = {'_id': 0}
    
    # 执行查询，并进行分页
    data = db.mongodb.find(cname, filter_dict, projection) \
        .sort("sort", 1) \
        .skip((page_num - 1) * page_size) \
        .limit(page_size)
    
    # 返回结果
    return Resp.ok(
        data={
            'list': list(data),
            'total': db.mongodb.count_documents(cname, filter_dict)
        }
    )

@router.post("/")
def update(post_data: Optional[Dict[str, Any]] = {}):
    """
    更新或插入MongoDB集合中的数据
    
    参数:
    - post_data: 包含cname(集合名)和其他数据字段的字典
    
    返回:
    - 更新或插入的文档key
    """
    cname = post_data.pop('cname')
    
    # 根据不同情况处理数据
    if 'key' in post_data and post_data['key']:
        # 修改现有文档
        filter_dict = {'key': post_data['key']}
        db.mongodb.find_one_and_update(cname, filter_dict, {"$set": post_data})
    
    elif 'filter' in post_data and post_data['filter']:
        # 使用自定义过滤器查找并更新
        filter_dict = post_data['filter']
        data = db.mongodb.find(cname, filter_dict, {'_id': 0}).sort("sort", 1)
        
        if list(data):
            # 如果找到匹配的文档，则更新
            db.mongodb.find_one_and_update(cname, filter_dict, {"$set": post_data})
        else:
            # 如果没有找到匹配的文档，则新增
            post_data['key'] = str(uuid.uuid4())
            db.mongodb.insert_one(cname, post_data)
    
    else:
        # 没有指定key或filter，直接新增文档
        post_data['key'] = str(uuid.uuid4())
        db.mongodb.insert_one(cname, post_data)
    
    return Resp.ok(data=post_data['key'])

@router.delete("/")
def delete(cname: Optional[str] = '', key: Optional[str] = ''):
    """
    删除MongoDB集合中的数据
    
    参数:
    - cname: 集合名称
    - key: 要删除的文档的key
    
    返回:
    - 成功响应
    """
    filter_dict = {'key': key}
    db.mongodb.delete_many(cname, filter_dict)
    return Resp.ok()