from fastapi import APIRouter, Request
from typing import Optional, Dict, Any, List
import re
from datetime import datetime
import uuid
import logging
from database import db
from Resp import ok as Resp_ok
from utils.common import ensure_initialized, is_valid_date, is_number, handle_error

router = APIRouter(
    prefix="/mongodb",
    tags=["mongodb"],
    responses={404: {"description": "Not found"}},
)

# 配置日志记录器
logger = logging.getLogger(__name__)

def build_filter(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """构建MongoDB查询过滤器"""
    filter_dict = {}
    
    for key, value in query_params.items():
        if isinstance(value, list) and value:
            if value[0]:
                filter_dict[key] = {'$in': value}
                
            if len(value) == 2:
                if is_valid_date(value[0]) and is_valid_date(value[1]):
                    filter_dict[key] = {'$gte': value[0], '$lt': value[1]}
                elif None in value and (is_number(value[0]) or is_number(value[1])):
                    start = 0 if not is_number(value[0]) else value[0]
                    end = 9223372036854775806 if not is_number(value[1]) else value[1]
                    filter_dict[key] = {'$gte': start, '$lt': end}
                elif is_number(value[0]) and is_number(value[1]):
                    filter_dict[key] = {'$gte': value[0], '$lt': value[1]}
        
        elif isinstance(value, str) and value:
            if ',' not in value:
                filter_dict[key] = re.compile('.*' + value + '.*')
            else:
                search_terms = value.split(',')
                search_conditions = [{key: re.compile('.*' + term + '.*')} for term in search_terms]
                filter_dict['$or'] = search_conditions
        
        elif isinstance(value, int):
            filter_dict[key] = {'$eq': value}
    
    return filter_dict

@router.get("/")
@ensure_initialized()
async def query(request: Request):
    """查询MongoDB集合中的数据"""
    try:
        query_params = dict(request.query_params)
        
        cname = query_params.pop('cname')
        page_num = int(query_params.pop('pageNum'))
        page_size = int(query_params.pop('pageSize'))
        
        sort_param = query_params.pop('sort', 'createdTime:-1')
        sort_field, sort_order = sort_param.split(':') if ':' in sort_param else (sort_param, '-1')
        sort_order = int(sort_order)
        
        filter_dict = build_filter(query_params)
        projection = {'_id': 0}
        
        collection = db.mongodb.db[cname]
        cursor = collection.find(filter_dict, projection) \
            .sort(sort_field, sort_order) \
            .skip((page_num - 1) * page_size) \
            .limit(page_size)
        
        data = await cursor.to_list(length=page_size)
        total = await collection.count_documents(filter_dict)
        
        return Resp_ok(
            data={
                'list': data,
                'total': total
            }
        )
    except Exception as e:
        return handle_error(e)

@router.post("/")
@ensure_initialized()
async def update(post_data: Optional[Dict[str, Any]] = {}):
    """更新或插入MongoDB集合中的数据"""
    try:
        cname = post_data.pop('cname')
        collection = db.mongodb.db[cname]
        
        if 'key' in post_data and post_data['key']:
            filter_dict = {'key': post_data['key']}
            await collection.find_one_and_update(filter_dict, {"$set": post_data})
        
        elif 'filter' in post_data and post_data['filter']:
            filter_dict = post_data['filter']
            cursor = collection.find(filter_dict).sort("createdTime", -1)
            document = await cursor.to_list(length=1)
            
            if document:
                await collection.find_one_and_update(filter_dict, {"$set": post_data})
            else:
                post_data['key'] = str(uuid.uuid4())
                await collection.insert_one(post_data)
        
        else:
            post_data['key'] = str(uuid.uuid4())
            await collection.insert_one(post_data)
        
        return Resp_ok(data=post_data['key'])
    except Exception as e:
        return handle_error(e)

@router.delete("/")
@ensure_initialized()
async def delete(cname: Optional[str] = '', key: Optional[str] = ''):
    """删除MongoDB集合中的数据"""
    try:
        collection = db.mongodb.db[cname]
        filter_dict = {'key': key}
        await collection.delete_many(filter_dict)
        return Resp_ok()
    except Exception as e:
        return handle_error(e)