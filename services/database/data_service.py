import logging
import re
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from bson import ObjectId
from pymongo import ReturnDocument

from core.database import db
from core.config import settings
from core.utils import get_current_time, is_valid_date, is_number

logger = logging.getLogger(__name__)

# --- Private Helpers ---

def _validate_cname(cname: Optional[str]) -> str:
    if not cname:
        raise ValueError("必须提供集合名称(cname)")
    return cname

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

def _build_filter(query_params: Dict[str, Any]) -> Dict[str, Any]:
    filter_dict = {}

    for key, value in query_params.items():
        if not value:
            continue

        if key == 'isoDate' and isinstance(value, str):
            if ',' in value:
                date_parts = [term.strip() for term in value.split(',') if term.strip()]
                if len(date_parts) == 2:
                    start_date, end_date = date_parts
                    if is_valid_date(start_date) and is_valid_date(end_date):
                        published_filter = _build_published_date_filter(start_date, end_date)
                        if published_filter:
                            filter_dict.update(published_filter)
                        continue
            else:
                if is_valid_date(value):
                    published_filter = _build_published_date_filter(value, value)
                    if published_filter:
                        filter_dict.update(published_filter)
                        continue

        if hasattr(value, '__iter__') and not isinstance(value, (str, bytes, dict)):
            value_list = list(value) if not isinstance(value, list) else value
            if not value_list:
                continue

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

        elif isinstance(value, str):
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

        elif isinstance(value, (int, float, bool)):
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
    cname = params.get('cname')
    if not cname:
        raise ValueError("Collection name (cname) is required")
    
    query_params = params.copy()
    del query_params['cname']
    
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
    cname = _validate_cname(cname)
    
    fields_param = query_params.pop('fields', None) or query_params.pop('select', None)
    exclude_fields_param = query_params.pop('excludeFields', None) or query_params.pop('exclude', None)

    try:
        page_num = max(1, int(query_params.pop('pageNum', 1)))
        page_size = min(8000, max(1, int(query_params.pop('pageSize', 2000))))
    except ValueError:
        raise ValueError("分页参数必须是有效的整数")

    sort_param = query_params.pop('orderBy', 'timestamp' if cname == 'apis' else 'order')
    sort_order = -1 if query_params.pop('orderType', 'asc').lower() == 'desc' else 1

    filter_dict = _build_filter(query_params)
    logger.info(f"Querying collection: {cname}, Filter: {filter_dict}")
    sort_list = _build_sort_list(sort_param, sort_order)
    
    projection = {'_id': 0}
    if fields_param:
        fields = [f.strip() for f in str(fields_param).split(',') if f.strip()]
        if 'key' not in fields:
            fields.append('key')
        projection = {'_id': 0, **{f: 1 for f in fields}}
    elif exclude_fields_param:
        exclude_fields = [f.strip() for f in str(exclude_fields_param).split(',') if f.strip()]
        projection = {'_id': 0, **{f: 0 for f in exclude_fields}}

    collection = db.db[cname]
    
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
    cname = params.get('cname')
    doc_id = params.get('id')
    
    if not cname or not doc_id:
        raise ValueError("cname and id are required")
        
    await db.initialize()
    collection = db.db[cname]
    document = await collection.find_one({'key': doc_id}, {'_id': 0})

    if not document:
        raise ValueError(f"未找到ID为 {doc_id} 的数据")
    
    return document

async def create_document(params: Dict[str, Any]) -> Dict[str, Any]:
    cname = params.get('cname')
    data = params.get('data')
    
    if not cname:
        raise ValueError("Collection name (cname) is required")
        
    if data is None:
        data = params.copy()
        del data['cname']

    await db.initialize()
    cname = _validate_cname(cname)
    if not data:
        raise ValueError("创建数据不能为空")

    collection = db.db[cname]

    if cname == 'rss':
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
            if cname == 'rss':
                raise ValueError(f"link 字段值 '{data_copy.get('link', '')}' 已存在，不能重复创建")
            else:
                raise ValueError(f"数据创建失败: 唯一性约束冲突")
        raise

    return {'key': data_copy['key']}

async def update_document(params: Dict[str, Any]) -> Dict[str, Any]:
    cname = params.get('cname')
    data = params.get('data')
    
    if not cname:
        raise ValueError("Collection name (cname) is required")
    if data is None:
        data = params.copy()
        del data['cname']

    await db.initialize()
    cname = _validate_cname(cname)
    
    key = data.get('key')
    link = data.get('link')
    content = data.get('content')

    if key:
        query_filter = {'key': key}
        identifier = key
        identifier_type = 'key'
    elif link:
        query_filter = {'link': link}
        identifier = link
        identifier_type = 'link'
    else:
        raise ValueError("更新数据时必须提供key字段或link字段")

    excluded_fields = ['key'] if key else []
    data_for_check = {k: v for k, v in data.items() if k not in excluded_fields}
    if not data_for_check:
        raise ValueError("更新数据不能为空")

    collection = db.db[cname]

    if cname == settings.collection_rss:
        new_link = data.get('link')
        if new_link:
            existing_item = await collection.find_one({'link': new_link})
            if existing_item:
                existing_key = existing_item.get('key')
                if key:
                    if existing_key != key:
                        raise ValueError(f"link 字段值 '{new_link}' 已被其他记录使用（key: {existing_key}）")
                elif link:
                    if new_link != link and existing_key:
                        raise ValueError(f"link 字段值 '{new_link}' 已被其他记录使用（key: {existing_key}）")
        
        if key:
            data['key'] = key
        
        if content:
            data['contentHash'] = hashlib.md5(content.encode('utf-8')).hexdigest()

    update_data = {k: v for k, v in data.items() if k not in (['key'] if key else [])}
    update_data['updatedTime'] = get_current_time()

    try:
        result = await collection.find_one_and_update(
            query_filter,
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
    except Exception as e:
        if 'duplicate key' in str(e).lower() or 'E11000' in str(e):
            if cname == settings.collection_rss:
                new_link = data.get('link')
                raise ValueError(f"link 字段值 '{new_link}' 已存在，不能重复")
            else:
                raise ValueError(f"数据更新失败: 唯一性约束冲突")
        raise

    if not result:
        raise ValueError(f"未找到{identifier_type}为 {identifier} 的数据")

    return {'key': result.get('key', identifier)}

async def delete_document(params: Dict[str, Any]) -> Dict[str, Any]:
    cname = params.get('cname')
    doc_id = params.get('id')
    
    if not cname or not doc_id:
        raise ValueError("cname and id are required")
        
    await db.initialize()
    cname = _validate_cname(cname)
    
    collection = db.db[cname]
    result = await collection.delete_one({'key': doc_id})
    
    if result.deleted_count == 0:
        raise ValueError(f"未找到ID为 {doc_id} 的数据，删除失败")
        
    return {'success': True}

async def upsert_document(params: Dict[str, Any]) -> Dict[str, Any]:
    cname = params.get('cname')
    filter_dict = params.get('filter')
    update_data = params.get('update')
    
    if not cname or not filter_dict or not update_data:
        raise ValueError("cname, filter, and update are required")
        
    await db.initialize()
    collection = db.db[cname]
    
    if '$set' not in update_data:
        update_data['$set'] = {}
    update_data['$set']['updatedTime'] = get_current_time()
    
    if '$setOnInsert' not in update_data:
        update_data['$setOnInsert'] = {}
    update_data['$setOnInsert']['createdTime'] = get_current_time()
    if 'key' not in update_data['$setOnInsert']:
        update_data['$setOnInsert']['key'] = str(uuid.uuid4())
    
    result = await collection.update_one(filter_dict, update_data, upsert=True)
    
    return {
        "matched_count": result.matched_count,
        "modified_count": result.modified_count,
        "upserted_id": str(result.upserted_id) if result.upserted_id else None
    }
