import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from bson import ObjectId

from core.database import db
from core.settings import settings
from core.utils import get_current_time, is_valid_date, is_number

logger = logging.getLogger(__name__)

# --- Private Helpers ---

def _validate_collection_name(collection_name: Optional[str]) -> str:
    if not collection_name:
        raise ValueError("必须提供集合名称(collection_name)")
    return collection_name

def _build_published_date_filter(start_date: str, end_date: str) -> Dict[str, Any]:
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        date_patterns = []
        iso_date_values = []
        current_dt = start_dt

        while current_dt <= end_dt:
            year, month, day = current_dt.year, current_dt.month, current_dt.day
            month_name = month_names[month - 1]
            date_patterns.extend([
                f'{year}-{month:02d}-{day:02d}',
                f'{day:02d} {month_name} {year}',
                f'{day} {month_name} {year}',
            ])
            iso_date_values.append(f'{year}-{month:02d}-{day:02d}')
            current_dt += timedelta(days=1)

        date_patterns = list(set(date_patterns))
        iso_date_values = list(set(iso_date_values))

        if not date_patterns:
            return {}

        or_conditions = []
        for pattern in date_patterns:
            or_conditions.append({'pubDate': {'$regex': pattern, '$options': 'i'}})
            or_conditions.append({'published': {'$regex': pattern, '$options': 'i'}})

        if iso_date_values:
            or_conditions.append({'isoDate': {'$in': iso_date_values}})
            for iso_date in iso_date_values:
                or_conditions.append({'isoDate': {'$regex': iso_date, '$options': 'i'}})

        return {'$or': or_conditions}
    except ValueError:
        return {}

def _handle_iso_date_filter(key: str, value: Any, filter_dict: Dict[str, Any]) -> bool:
    """处理 isoDate 特殊过滤逻辑"""
    if key != 'isoDate' or not isinstance(value, str):
        return False

    if ',' in value:
        date_parts = [term.strip() for term in value.split(',') if term.strip()]
        if len(date_parts) == 2:
            start_date, end_date = date_parts
            if is_valid_date(start_date) and is_valid_date(end_date):
                published_filter = _build_published_date_filter(start_date, end_date)
                if published_filter:
                    filter_dict.update(published_filter)
                return True
    else:
        if is_valid_date(value):
            published_filter = _build_published_date_filter(value, value)
            if published_filter:
                filter_dict.update(published_filter)
            return True
    return False

def _handle_range_or_list_filter(key: str, value: Any, filter_dict: Dict[str, Any]) -> bool:
    """处理范围查询或列表查询"""
    if not (hasattr(value, '__iter__') and not isinstance(value, (str, bytes, dict))):
        return False
        
    value_list = list(value) if not isinstance(value, list) else value
    if not value_list:
        return True

    if len(value_list) == 2:
        start, end = value_list
        if is_valid_date(start) and is_valid_date(end):
            filter_dict[key] = {'$gte': start, '$lt': end}
        elif is_number(start) and is_number(end):
            filter_dict[key] = {'$gte': float(start), '$lt': float(end)}
        elif is_number(start):
            filter_dict[key] = {'$gte': float(start)}
        elif is_number(end):
            filter_dict[key] = {'$lt': float(end)}
    else:
        filter_dict[key] = {'$in': value_list}
    return True

def _handle_string_search_filter(key: str, value: Any, filter_dict: Dict[str, Any]) -> bool:
    """处理字符串模糊查询"""
    if not isinstance(value, str):
        return False
        
    if ',' in value:
        search_terms = [term.strip() for term in value.split(',') if term.strip()]
        if search_terms:
            if '$or' in filter_dict:
                filter_dict['$or'].extend([
                    {key: re.compile(f'.*{re.escape(term)}.*', re.IGNORECASE)}
                    for term in search_terms
                ])
            else:
                filter_dict['$or'] = [
                    {key: re.compile(f'.*{re.escape(term)}.*', re.IGNORECASE)}
                    for term in search_terms
                ]
    else:
        filter_dict[key] = re.compile(f'.*{re.escape(value)}.*', re.IGNORECASE)
    return True

def _build_filter(query_params: Dict[str, Any]) -> Dict[str, Any]:
    filter_dict = {}

    for key, value in query_params.items():
        if not value:
            continue

        # key 字段使用精确匹配
        if key == 'key' and isinstance(value, str):
            filter_dict[key] = value
            continue

        if _handle_iso_date_filter(key, value, filter_dict):
            continue

        if _handle_range_or_list_filter(key, value, filter_dict):
            continue

        if _handle_string_search_filter(key, value, filter_dict):
            continue

        if isinstance(value, (int, float, bool)):
            filter_dict[key] = value

    return filter_dict

def _build_sort_list(sort_param: str, sort_order: int) -> List[tuple]:
    sort_list = []
    if sort_param == 'order':
        sort_list.append(('order', 1))
    else:
        sort_list.append((sort_param, sort_order))

    if sort_param != 'updatedTime':
        sort_list.append(('updatedTime', -1))
    if sort_param != 'createdTime':
        sort_list.append(('createdTime', -1))
    
    return sort_list

# --- Public Service Methods ---

async def query_documents(params: Dict[str, Any]) -> Dict[str, Any]:
    # 支持 cname 和 collection_name
    collection_name = params.get('collection_name') or params.get('cname')
    if not collection_name:
        raise ValueError("Collection name (collection_name/cname) is required")
    
    query_params = params.copy()
    query_params.pop('cname', None)
    query_params.pop('collection_name', None)
    
    # 处理 filter 参数：如果存在 filter 参数，将其内容合并到查询参数中
    filter_param = query_params.pop('filter', None)
    if filter_param and isinstance(filter_param, dict):
        # 将 filter 中的内容合并到 query_params 中
        query_params.update(filter_param)
    
    # 兼容旧参数
    try:
        if 'limit' in query_params and 'pageSize' not in query_params:
            query_params['pageSize'] = int(query_params.pop('limit'))
        else:
            query_params.pop('limit', None)
    except:
        query_params.pop('limit', None)
    
    try:
        if 'page' in query_params and 'pageNum' not in query_params:
            query_params['pageNum'] = int(query_params.pop('page'))
        else:
            query_params.pop('page', None)
    except:
        query_params.pop('page', None)

    await db.initialize()
    collection_name = _validate_collection_name(collection_name)
    
    fields_param = query_params.pop('fields', None) or query_params.pop('select', None)
    exclude_fields_param = query_params.pop('excludeFields', None) or query_params.pop('exclude', None)

    try:
        page_num = max(1, int(query_params.pop('pageNum', 1)))
        page_size = min(8000, max(1, int(query_params.pop('pageSize', 2000))))
    except ValueError:
        raise ValueError("分页参数必须是有效的整数")

    sort_param = query_params.pop('orderBy', 'timestamp' if collection_name == 'apis' else 'order')
    sort_order = -1 if query_params.pop('orderType', 'asc').lower() == 'desc' else 1

    filter_dict = _build_filter(query_params)
    logger.info(f"Querying collection: {collection_name}, Filter: {filter_dict}")
    sort_list = _build_sort_list(sort_param, sort_order)
    
    projection = {'_id': 0}
    if fields_param:
        fields = [f.strip() for f in str(fields_param).split(',') if f.strip()]
        if 'key' not in fields:
            fields.append('key')
        if collection_name == 'sessions':
            fields = [f for f in fields if f != 'pageContent']
        projection = {'_id': 0, **{f: 1 for f in fields}}
    elif exclude_fields_param:
        exclude_fields = [f.strip() for f in str(exclude_fields_param).split(',') if f.strip()]
        if collection_name == 'sessions' and 'pageContent' not in exclude_fields:
            exclude_fields.append('pageContent')
        projection = {'_id': 0, **{f: 0 for f in exclude_fields}}
    elif collection_name == 'sessions':
        projection = {'_id': 0, 'pageContent': 0}

    collection = db.db[collection_name]
    
    cursor = collection.find(filter_dict, projection) \
        .sort(sort_list) \
        .skip((page_num - 1) * page_size) \
        .limit(page_size)

    data = [doc async for doc in cursor]
    total = await collection.count_documents(filter_dict)
    total_pages = (total + page_size - 1) // page_size

    return {
        'list': data,
        'total': total,
        'pageNum': page_num,
        'pageSize': page_size,
        'totalPages': total_pages
    }

async def get_document_detail(params: Dict[str, Any]) -> Dict[str, Any]:
    collection_name = params.get('collection_name') or params.get('cname')
    doc_id = params.get('id')
    
    if not collection_name or not doc_id:
        raise ValueError("collection_name/cname and id are required")
        
    await db.initialize()
    collection = db.db[collection_name]
    projection = {'_id': 0}
    if collection_name == 'sessions':
        projection['pageContent'] = 0
    document = await collection.find_one({'key': doc_id}, projection)

    if not document:
        raise ValueError(f"未找到ID为 {doc_id} 的数据")
    
    return document

async def create_document(params: Dict[str, Any]) -> Dict[str, Any]:
    collection_name = params.get('collection_name') or params.get('cname')
    data = params.get('data')
    
    if not collection_name:
        raise ValueError("Collection name (collection_name/cname) is required")
        
    if data is None:
        data = params.copy()
        data.pop('cname', None)
        data.pop('collection_name', None)

    await db.initialize()
    collection_name = _validate_collection_name(collection_name)
    if not data:
        raise ValueError("创建数据不能为空")

    collection = db.db[collection_name]

    if collection_name == 'rss':
        link = data.get('link')
        if link:
            existing_item = await collection.find_one({'link': link})
            if existing_item:
                raise ValueError(f"link 字段值 '{link}' 已存在，不能重复创建")

    data_copy = {k: (str(v) if isinstance(v, ObjectId) else v) for k, v in data.items()}
    current_time = get_current_time()
    data_copy.update({
        'key': str(uuid.uuid4()),
        'createdTime': current_time,
        'updatedTime': current_time
    })
    if collection_name == 'sessions':
        data_copy.pop('pageContent', None)

    try:
        max_order_doc = await collection.find_one(
            sort=[("order", -1)],
            projection={"order": 1}
        )
        max_order = max_order_doc.get("order", 0) if max_order_doc else 0
        data_copy['order'] = max_order + 1
    except Exception as e:
        logger.warning(f"获取最大排序值失败: {str(e)}")
        data_copy['order'] = 1

    try:
        await collection.insert_one(data_copy)
    except Exception as e:
        if 'duplicate key' in str(e).lower() or 'E11000' in str(e):
            if collection_name == 'rss':
                raise ValueError(f"link 字段值 '{data_copy.get('link', '')}' 已存在，不能重复创建")
            else:
                raise ValueError(f"数据创建失败: 唯一性约束冲突")
        raise

    return {'key': data_copy['key']}

async def update_document(params: Dict[str, Any]) -> Dict[str, Any]:
    collection_name = params.get('collection_name') or params.get('cname')
    data = params.get('data')
    
    if not collection_name:
        raise ValueError("Collection name (collection_name/cname) is required")
    if data is None:
        data = params.copy()
        data.pop('cname', None)
        data.pop('collection_name', None)

    await db.initialize()
    collection_name = _validate_collection_name(collection_name)
    
    doc_id = data.get('key')
    if not doc_id:
        raise ValueError("更新数据必须包含 key 字段")
        
    collection = db.db[collection_name]
    
    # 检查是否存在
    existing_doc = await collection.find_one({'key': doc_id})
    if not existing_doc:
        raise ValueError(f"未找到ID为 {doc_id} 的数据")
        
    # 移除不可更新字段
    update_data = data.copy()
    update_data.pop('_id', None)
    update_data.pop('key', None)
    update_data.pop('createdTime', None)
    if collection_name == 'sessions':
        update_data.pop('pageContent', None)
    
    update_data['updatedTime'] = get_current_time()
    
    await collection.update_one(
        {'key': doc_id},
        {'$set': update_data}
    )
    
    return {'key': doc_id, 'updated': True}

async def upsert_document(params: Dict[str, Any]) -> Dict[str, Any]:
    collection_name = params.get('collection_name') or params.get('cname')
    filter_doc = params.get('filter')
    update_doc = params.get('update')
    
    if not collection_name:
        raise ValueError("Collection name (collection_name/cname) is required")
    if not filter_doc:
        raise ValueError("Filter (filter) is required")
    if not update_doc:
        raise ValueError("Update data (update) is required")

    await db.initialize()
    collection_name = _validate_collection_name(collection_name)
    collection = db.db[collection_name]
    
    # 确保 update_doc 包含 atomic operators
    if not any(k.startswith('$') for k in update_doc.keys()):
        # 如果没有操作符，假设是 $set
        update_doc = {'$set': update_doc}

    # 强制添加系统字段
    if '$set' not in update_doc:
        update_doc['$set'] = {}
    update_doc['$set']['updatedTime'] = get_current_time()
    
    if '$setOnInsert' not in update_doc:
        update_doc['$setOnInsert'] = {}
    update_doc['$setOnInsert']['createdTime'] = get_current_time()
    
    if 'key' not in update_doc['$setOnInsert']:
        update_doc['$setOnInsert']['key'] = str(uuid.uuid4())
    if collection_name == 'sessions':
        if isinstance(update_doc.get('$set'), dict):
            update_doc['$set'].pop('pageContent', None)
        if isinstance(update_doc.get('$setOnInsert'), dict):
            update_doc['$setOnInsert'].pop('pageContent', None)

    result = await collection.update_one(filter_doc, update_doc, upsert=True)
    
    return {
        "matched_count": result.matched_count,
        "modified_count": result.modified_count,
        "upserted_id": str(result.upserted_id) if result.upserted_id else None
    }

async def delete_document(params: Dict[str, Any]) -> Dict[str, Any]:
    collection_name = params.get('collection_name') or params.get('cname')
    doc_id = params.get('key') or params.get('id')
    
    if not collection_name or not doc_id:
        raise ValueError("collection_name/cname and key are required")
        
    await db.initialize()
    collection_name = _validate_collection_name(collection_name)
    collection = db.db[collection_name]
    
    result = await collection.delete_one({'key': doc_id})
    
    if result.deleted_count == 0:
        raise ValueError(f"未找到ID为 {doc_id} 的数据或删除失败")
        
    return {'key': doc_id, 'deleted': True}
