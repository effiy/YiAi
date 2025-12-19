from functools import wraps
from fastapi import APIRouter, Request, Body, HTTPException
from typing import Dict, Any, List, Optional
import re
from datetime import datetime, timedelta
import uuid
import logging
from bson import ObjectId
from Resp import RespOk
from pymongo import UpdateOne, ReturnDocument

from database import db

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
            if not hasattr(db, '_initialized') or not db._initialized:
                logger.info("正在初始化数据库连接")
                await db.initialize()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def is_valid_date(date_str: str) -> bool:
    """检查字符串是否为有效日期格式"""
    if not isinstance(date_str, str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def is_number(value: Any) -> bool:
    """检查值是否为数字"""
    if value is None:
        return False
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

def create_response(code: int, message: str, data: Any = None) -> dict:
    """统一的响应格式"""
    return {
        "code": code,
        "message": message,
        "data": data
    }

def handle_error(e: Exception, status_code: int = 500) -> dict:
    """统一的错误处理"""
    error_msg = str(e)
    logger.error(f"发生错误: {error_msg}")
    return create_response(
        code=status_code,
        message=error_msg,
        data=None
    )

def parse_published_date(date_str: str) -> Optional[datetime]:
    """解析 published 字段中的日期字符串，支持多种格式"""
    if not date_str:
        return None
    
    # 尝试解析常见的日期格式
    date_formats = [
        '%a, %d %b %Y %H:%M:%S %z',  # Mon, 01 Dec 2025 13:25:44 +0800
        '%a, %d %b %Y %H:%M:%S',     # Mon, 01 Dec 2025 13:25:44
        '%Y-%m-%d %H:%M:%S',         # 2025-12-01 13:25:44
        '%Y-%m-%d',                   # 2025-12-01
        '%d %b %Y',                   # 01 Dec 2025
        '%Y-%m-%dT%H:%M:%S',         # 2025-12-01T13:25:44
        '%Y-%m-%dT%H:%M:%S%z',       # 2025-12-01T13:25:44+0800
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def build_published_date_filter(start_date: str, end_date: str) -> Dict[str, Any]:
    """构建 pubDate 和 isoDate 字段的日期范围查询，兼容多种日期格式"""
    try:
        # 解析开始和结束日期
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 月份名称映射
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # 生成日期范围内的所有日期模式
        date_patterns = []
        iso_date_values = []  # 用于 isoDate 字段的精确匹配
        current_dt = start_dt
        
        while current_dt <= end_dt:
            year = current_dt.year
            month = current_dt.month
            day = current_dt.day
            month_name = month_names[month - 1]
            
            # 生成该日期的所有可能格式（用于 pubDate 字段的正则匹配）
            date_patterns.extend([
                f'{year}-{month:02d}-{day:02d}',  # 2025-12-01
                f'{day:02d} {month_name} {year}',  # 01 Dec 2025
                f'{day} {month_name} {year}',     # 1 Dec 2025
            ])
            
            # 用于 isoDate 字段的精确匹配值
            iso_date_values.append(f'{year}-{month:02d}-{day:02d}')
            
            # 移动到下一天
            current_dt += timedelta(days=1)
        
        # 去重
        date_patterns = list(set(date_patterns))
        iso_date_values = list(set(iso_date_values))
        
        if not date_patterns:
            return {}
        
        # 构建查询条件：同时匹配 pubDate、published 和 isoDate 字段
        # pubDate/published 字段使用正则表达式匹配（支持 'Sun, 29 Jun 2025 08:19:20 GMT' 等格式）
        # isoDate 字段使用精确匹配或范围匹配
        or_conditions = []
        
        # 添加 pubDate 字段的正则匹配条件（兼容 pubDate 字段）
        for pattern in date_patterns:
            or_conditions.append({'pubDate': {'$regex': pattern, '$options': 'i'}})
        
        # 添加 published 字段的正则匹配条件（兼容 published 字段，RSS 数据可能使用此字段）
        for pattern in date_patterns:
            or_conditions.append({'published': {'$regex': pattern, '$options': 'i'}})
        
        # 添加 isoDate 字段的匹配条件（如果字段存在）
        if iso_date_values:
            # 使用 $in 进行精确匹配
            or_conditions.append({'isoDate': {'$in': iso_date_values}})
            # 也支持 isoDate 字段包含日期字符串的情况（使用正则）
            for iso_date in iso_date_values:
                or_conditions.append({'isoDate': {'$regex': iso_date, '$options': 'i'}})
        
        # 使用 $or 组合所有条件
        return {
            '$or': or_conditions
        }
    except ValueError:
        # 如果日期解析失败，返回空查询
        return {}

def build_filter(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """构建MongoDB查询过滤条件"""
    filter_dict = {}

    for key, value in query_params.items():
        if not value:  # 跳过空值
            continue

        # 特殊处理 isoDate 参数（用于 RSS 查询）
        # isoDate 查询会匹配 pubDate 字段中包含指定日期的记录
        if key == 'isoDate' and isinstance(value, str):
            if ',' in value:
                # 日期范围查询，格式：2025-12-01,2025-12-01
                date_parts = [term.strip() for term in value.split(',') if term.strip()]
                if len(date_parts) == 2:
                    start_date, end_date = date_parts
                    if is_valid_date(start_date) and is_valid_date(end_date):
                        # 构建 pubDate 字段的日期查询
                        published_filter = build_published_date_filter(start_date, end_date)
                        if published_filter:
                            # pubDate 字段的查询作为独立的 AND 条件
                            # 因为 pubDate 可能有多种格式，所以内部使用 $or
                            filter_dict.update(published_filter)
                        continue
            else:
                # 单个日期查询
                if is_valid_date(value):
                    published_filter = build_published_date_filter(value, value)
                    if published_filter:
                        # pubDate 字段的查询作为独立的 AND 条件
                        filter_dict.update(published_filter)
                        continue

        # 处理列表类型参数
        if hasattr(value, '__iter__') and not isinstance(value, (str, bytes, dict)):
            value_list = list(value) if not isinstance(value, list) else value

            if not value_list:  # 跳过空列表
                continue

            if len(value_list) == 2:  # 范围查询
                start, end = value_list
                if is_valid_date(start) and is_valid_date(end):
                    filter_dict[key] = {'$gte': start, '$lt': end}
                elif is_number(start) and is_number(end):
                    filter_dict[key] = {'$gte': float(start), '$lt': float(end)}
                elif is_number(start):
                    filter_dict[key] = {'$gte': float(start)}
                elif is_number(end):
                    filter_dict[key] = {'$lt': float(end)}
            else:  # 多值查询
                filter_dict[key] = {'$in': value_list}

        elif isinstance(value, str):
            if ',' in value:  # 多条件模糊查询
                search_terms = [term.strip() for term in value.split(',') if term.strip()]
                if search_terms:
                    # 合并到 $or 条件中
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
            else:  # 单条件模糊查询
                filter_dict[key] = re.compile(f'.*{re.escape(value)}.*', re.IGNORECASE)

        elif isinstance(value, (int, float, bool)):
            filter_dict[key] = value

    return filter_dict

def get_current_time() -> str:
    """获取当前UTC时间字符串"""
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

def validate_collection_name(cname: Optional[str]) -> str:
    """验证集合名称"""
    if not cname:
        raise ValueError("必须提供集合名称(cname)")
    return cname

def build_sort_list(sort_param: str, sort_order: int) -> List[tuple]:
    """构建排序列表"""
    sort_list = []

    if sort_param == 'order':
        sort_list.append(('order', 1))  # 默认按order字段升序
    else:
        sort_list.append((sort_param, sort_order))

    # 添加次要排序条件
    if sort_param != 'updatedTime':
        sort_list.append(('updatedTime', -1))
    if sort_param != 'createdTime':
        sort_list.append(('createdTime', -1))

    return sort_list

@router.get("/")
@ensure_initialized()
async def query(request: Request):
    try:
        query_params = dict(request.query_params)

        # 验证并获取集合名称
        cname = validate_collection_name(query_params.pop('cname', None))

        # 字段投影（用于节约流量/提高查询性能）
        # - fields: 逗号分隔的字段白名单（包含模式）
        # - excludeFields: 逗号分隔的字段黑名单（排除模式）
        # 注意：MongoDB 投影要么包含要么排除（_id 例外），两者不能混用
        fields_param = query_params.pop('fields', None) or query_params.pop('select', None)
        exclude_fields_param = query_params.pop('excludeFields', None) or query_params.pop('exclude', None)

        # 验证分页参数
        try:
            page_num = max(1, int(query_params.pop('pageNum', 1)))
            # 默认不要全量拉取，避免一次返回超大列表导致流量和延迟爆炸
            # 需要更多数据时由调用方显式传入 pageSize/pageNum 分页拉取
            page_size = min(8000, max(1, int(query_params.pop('pageSize', 2000))))
        except ValueError:
            raise ValueError("分页参数必须是有效的整数")

        # 验证排序参数
        # apis 集合通常按 timestamp 倒序更符合使用习惯
        sort_param = query_params.pop('orderBy', 'timestamp' if cname == 'apis' else 'order')
        sort_order = -1 if query_params.pop('orderType', 'asc').lower() == 'desc' else 1

        # 构建查询条件和排序
        filter_dict = build_filter(query_params)
        sort_list = build_sort_list(sort_param, sort_order)
        projection = {'_id': 0}

        # 若调用方未指定投影，针对 apis 默认排除大字段（列表页通常不需要这些字段）
        # 需要详情时建议调用 /mongodb/detail 获取单条完整数据
        if cname == 'apis' and not fields_param and not exclude_fields_param:
            exclude_fields_param = 'headers,body,responseHeaders,responseText,responseBody,curl'

        # 应用投影
        if fields_param:
            fields = [f.strip() for f in str(fields_param).split(',') if f.strip()]
            # key 是前端普遍依赖的稳定标识，确保带上
            if 'key' not in fields:
                fields.append('key')
            projection = {'_id': 0, **{f: 1 for f in fields}}
        elif exclude_fields_param:
            exclude_fields = [f.strip() for f in str(exclude_fields_param).split(',') if f.strip()]
            # 排除模式下保持默认 _id=0，同时排除指定字段
            projection = {'_id': 0, **{f: 0 for f in exclude_fields}}

        # 执行查询
        collection = db.mongodb.db[cname]

        cursor = collection.find(filter_dict, projection) \
            .sort(sort_list) \
            .skip((page_num - 1) * page_size) \
            .limit(page_size)

        # 获取数据和总数
        data = [doc async for doc in cursor]
        total = await collection.count_documents(filter_dict)
        total_pages = (total + page_size - 1) // page_size

        return RespOk(
            data={
                'list': data,
                'total': total,
                'pageNum': page_num,
                'pageSize': page_size,
                'totalPages': total_pages
            }
        )
    except ValueError as e:
        logger.warning(f"参数验证失败: {str(e)}")
        return handle_error(e, 400)
    except Exception as e:
        logger.error(f"查询数据失败: {str(e)}", exc_info=True)
        return handle_error(e)

@router.get("/detail")
@ensure_initialized()
async def get_detail(cname: str, id: str):
    """获取MongoDB集合中的单条数据详情"""
    try:
        collection = db.mongodb.db[cname]
        document = await collection.find_one({'key': id}, {'_id': 0})

        if not document:
            raise ValueError(f"未找到ID为 {id} 的数据")

        return RespOk(data=document)
    except ValueError as e:
        logger.warning(f"获取详情失败: {str(e)}")
        return handle_error(e, 404)
    except Exception as e:
        logger.error(f"获取详情失败: {str(e)}", exc_info=True)
        return handle_error(e)

@router.post("/")
@ensure_initialized()
async def create(request: Request, data: Dict[str, Any] = Body(...)):
    """创建MongoDB集合数据"""
    try:
        # 获取集合名称
        query_params = dict(request.query_params)
        cname = query_params.get('cname')

        if not cname and 'cname' in data:
            cname = data.pop('cname')

        cname = validate_collection_name(cname)

        if not data:
            raise ValueError("创建数据不能为空")

        collection = db.mongodb.db[cname]
        logger.info(f"创建数据请求 - 集合: {cname}, 数据: {data}")

        # 如果是 rss 集合，检查 link 字段的唯一性
        if cname == 'rss':
            link = data.get('link')
            if link:
                existing_item = await collection.find_one({'link': link})
                if existing_item:
                    raise ValueError(f"link 字段值 '{link}' 已存在，不能重复创建")

        # 准备数据
        data_copy = {k: (str(v) if isinstance(v, ObjectId) else v) for k, v in data.items()}

        # 生成基础字段
        current_time = get_current_time()
        data_copy.update({
            'key': str(uuid.uuid4()),
            'createdTime': current_time,
            'updatedTime': current_time
        })

        # 设置排序值
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

        # 插入数据
        try:
            result = await collection.insert_one(data_copy)
            logger.info(f"数据创建成功 - 集合: {cname}, ID: {result.inserted_id}")
        except Exception as e:
            # 捕获唯一索引冲突错误
            if 'duplicate key' in str(e).lower() or 'E11000' in str(e):
                if cname == 'rss':
                    raise ValueError(f"link 字段值 '{data_copy.get('link', '')}' 已存在，不能重复创建")
                else:
                    raise ValueError(f"数据创建失败: 唯一性约束冲突")
            raise

        return RespOk(data={'key': data_copy['key']})

    except ValueError as e:
        logger.warning(f"数据验证失败: {str(e)}")
        return handle_error(e, 400)
    except Exception as e:
        logger.error(f"创建数据失败: {str(e)}", exc_info=True)
        return handle_error(e)

@router.put("/")
@ensure_initialized()
async def update(request: Request, data: Dict[str, Any] = Body(...)):
    """更新MongoDB集合数据"""
    try:
        # 获取集合名称
        query_params = dict(request.query_params)
        cname = query_params.get('cname')

        if not cname and 'cname' in data:
            cname = data.pop('cname')

        cname = validate_collection_name(cname)

        # 验证key字段或link字段
        key = data.get('key')
        link = data.get('link')
        
        # 确定查询条件和使用的标识字段
        if key:
            # 优先使用key字段
            query_filter = {'key': key}
            identifier = key
            identifier_type = 'key'
        elif link:
            # 兼容使用link字段替换key字段
            query_filter = {'link': link}
            identifier = link
            identifier_type = 'link'
        else:
            raise ValueError("更新数据时必须提供key字段或link字段")

        # 检查是否有有效的更新数据
        # 如果使用key查找，排除key字段（因为key是查找条件，不应该被更新）
        # 如果使用link查找，允许更新link字段（因为link字段的值可能会改变）
        excluded_fields = ['key'] if key else []
        data_for_check = {k: v for k, v in data.items() if k not in excluded_fields}
        if not data_for_check:
            raise ValueError("更新数据不能为空")

        collection = db.mongodb.db[cname]

        # 如果是 rss 集合，且要更新 link 字段，检查新 link 值的唯一性
        if cname == 'rss':
            new_link = data.get('link')
            if new_link:
                # 查找是否存在其他记录使用了相同的 link
                existing_item = await collection.find_one({'link': new_link})
                if existing_item:
                    # 如果找到的记录不是当前要更新的记录，则冲突
                    existing_key = existing_item.get('key')
                    existing_link = existing_item.get('link')
                    if key:
                        # 使用 key 查找时，检查找到的记录是否就是当前记录
                        if existing_key != key:
                            raise ValueError(f"link 字段值 '{new_link}' 已被其他记录使用（key: {existing_key}）")
                    elif link:
                        # 使用 link 查找时，如果 link 值改变，检查新值是否冲突
                        if new_link != link and existing_key:
                            raise ValueError(f"link 字段值 '{new_link}' 已被其他记录使用（key: {existing_key}）")

        # 准备更新数据
        # 如果使用key查找，排除key字段（避免更新主键），但允许更新link字段
        # 如果使用link查找，允许更新所有字段（包括key和link）
        update_data = {k: v for k, v in data.items() if k not in (['key'] if key else [])}
        update_data['updatedTime'] = get_current_time()

        # 执行更新
        try:
            result = await collection.find_one_and_update(
                query_filter,
                {"$set": update_data},
                return_document=ReturnDocument.AFTER
            )
        except Exception as e:
            # 捕获唯一索引冲突错误
            if 'duplicate key' in str(e).lower() or 'E11000' in str(e):
                if cname == 'rss':
                    new_link = data.get('link')
                    raise ValueError(f"link 字段值 '{new_link}' 已存在，不能重复")
                else:
                    raise ValueError(f"数据更新失败: 唯一性约束冲突")
            raise

        if not result:
            raise ValueError(f"未找到{identifier_type}为 {identifier} 的数据")

        # 返回实际使用的key值
        actual_key = result.get('key', identifier)
        return RespOk(data={"key": actual_key, "updated": True})

    except ValueError as e:
        logger.warning(f"数据验证失败: {str(e)}")
        return handle_error(e, 400)
    except Exception as e:
        logger.error(f"更新数据失败: {str(e)}", exc_info=True)
        return handle_error(e)

@router.delete("/")
@ensure_initialized()
async def delete(request: Request):
    """删除MongoDB集合中的数据"""
    try:
        query_params = dict(request.query_params)
        cname = validate_collection_name(query_params.get('cname'))
        key = query_params.get('key')
        link = query_params.get('link')
        keys_str = query_params.get('keys')
        links_str = query_params.get('links')

        collection = db.mongodb.db[cname]

        # 批量删除
        if keys_str:
            keys_list = [k.strip() for k in keys_str.split(',') if k.strip()]
            if not keys_list:
                raise ValueError("keys参数不能为空")

            result = await collection.delete_many({'key': {'$in': keys_list}})
            return RespOk(data={"deleted_count": result.deleted_count})
        
        elif links_str:
            links_list = [l.strip() for l in links_str.split(',') if l.strip()]
            if not links_list:
                raise ValueError("links参数不能为空")

            result = await collection.delete_many({'link': {'$in': links_list}})
            return RespOk(data={"deleted_count": result.deleted_count})

        # 单个删除
        elif key:
            # 优先使用key字段
            result = await collection.delete_one({'key': key})
            if result.deleted_count == 0:
                raise ValueError(f"未找到key为 {key} 的数据")
            return RespOk(data={"deleted_count": result.deleted_count})
        
        elif link:
            # 兼容使用link字段替换key字段
            result = await collection.delete_one({'link': link})
            if result.deleted_count == 0:
                raise ValueError(f"未找到link为 {link} 的数据")
            return RespOk(data={"deleted_count": result.deleted_count})

        else:
            raise ValueError("删除操作必须提供有效的key、link、keys或links参数")

    except ValueError as e:
        logger.warning(f"删除数据验证失败: {str(e)}")
        return handle_error(e, 400)
    except Exception as e:
        logger.error(f"删除数据失败: {str(e)}", exc_info=True)
        return handle_error(e)

@router.put("/batch-order")
@ensure_initialized()
async def batch_order(request: Request, data: Dict[str, Any] = Body(...)):
    """批量更新数据排序"""
    try:
        # 获取集合名称
        query_params = dict(request.query_params)
        cname = query_params.get('cname')

        if not cname and 'cname' in data:
            cname = data.pop('cname')

        cname = validate_collection_name(cname)

        # 验证排序数据
        orders = data.get('orders', [])
        if not isinstance(orders, list) or not orders:
            raise ValueError("必须提供有效的排序项列表(orders)")

        # 验证每个排序项
        for i, item in enumerate(orders):
            if not isinstance(item, dict):
                raise ValueError(f"排序项 {i+1} 必须是对象")
            if not item.get('key'):
                raise ValueError(f"排序项 {i+1} 必须提供有效的key")
            if 'order' not in item:
                raise ValueError(f"排序项 {i+1} 必须提供有效的order值")

        collection = db.mongodb.db[cname]

        # 构建批量更新操作
        update_time = get_current_time()
        operations = [
            UpdateOne(
                {'key': item['key']},
                {
                    '$set': {
                        'order': item['order'],
                        'updatedTime': update_time
                    }
                }
            )
            for item in orders
        ]

        # 执行批量更新
        result = await collection.bulk_write(operations)

        return RespOk(data={
            "updated_count": result.modified_count,
            "total_count": len(operations)
        })

    except ValueError as e:
        logger.warning(f"批量排序数据验证失败: {str(e)}")
        return handle_error(e, 400)
    except Exception as e:
        logger.error(f"批量排序失败: {str(e)}", exc_info=True)
        return handle_error(e)


