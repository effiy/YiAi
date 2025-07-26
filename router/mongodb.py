from functools import wraps
from fastapi import APIRouter, Request, Body, HTTPException
from typing import Dict, Any, List, Optional
import re
from datetime import datetime
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

def build_filter(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """构建MongoDB查询过滤条件"""
    filter_dict = {}

    for key, value in query_params.items():
        if not value:  # 跳过空值
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
    """查询MongoDB集合数据

    GET 请求：
    /mongodb/?cname=rss&isoDate=2025-06-21,2025-06-21

    参数说明：
    - cname: 集合名称（必需）
    - pageNum: 页码，默认为1
    - pageSize: 每页大小，默认为999999999
    - orderBy: 排序字段，默认为'order'
    - orderType: 排序方式，'asc'升序或'desc'降序，默认为'asc'
    - 其他参数用于过滤条件：
      - 字符串参数：支持模糊查询，多个值用逗号分隔
      - 日期范围：格式为 "开始日期,结束日期"，如 "2024-01-01,2024-12-31"
      - 数值范围：格式为 "最小值,最大值"，如 "10,100"
    """
    try:
        query_params = dict(request.query_params)

        # 验证并获取集合名称
        cname = validate_collection_name(query_params.pop('cname', None))

        # 验证分页参数
        try:
            page_num = max(1, int(query_params.pop('pageNum', 1)))
            page_size = min(999999999, max(1, int(query_params.pop('pageSize', 999999999))))
        except ValueError:
            raise ValueError("分页参数必须是有效的整数")

        # 验证排序参数
        sort_param = query_params.pop('orderBy', 'order')
        sort_order = -1 if query_params.pop('orderType', 'asc').lower() == 'desc' else 1

        # 构建查询条件和排序
        filter_dict = build_filter(query_params)
        sort_list = build_sort_list(sort_param, sort_order)
        projection = {'_id': 0}

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
        result = await collection.insert_one(data_copy)
        logger.info(f"数据创建成功 - 集合: {cname}, ID: {result.inserted_id}")

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

        # 验证key字段
        key = data.get('key')
        if not key:
            raise ValueError("更新数据时必须提供key字段")

        if len(data) <= 1:  # 只有key字段
            raise ValueError("更新数据不能为空")

        collection = db.mongodb.db[cname]

        # 添加更新时间
        data['updatedTime'] = get_current_time()

        # 执行更新
        result = await collection.find_one_and_update(
            {'key': key},
            {"$set": data},
            return_document=ReturnDocument.AFTER
        )

        if not result:
            raise ValueError(f"未找到key为 {key} 的数据")

        return RespOk(data={"key": key, "updated": True})

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
        keys_str = query_params.get('keys')

        collection = db.mongodb.db[cname]

        # 批量删除
        if keys_str:
            keys_list = [k.strip() for k in keys_str.split(',') if k.strip()]
            if not keys_list:
                raise ValueError("keys参数不能为空")

            result = await collection.delete_many({'key': {'$in': keys_list}})
            return RespOk(data={"deleted_count": result.deleted_count})

        # 单个删除
        elif key:
            result = await collection.delete_one({'key': key})
            if result.deleted_count == 0:
                raise ValueError(f"未找到key为 {key} 的数据")
            return RespOk(data={"deleted_count": result.deleted_count})

        else:
            raise ValueError("删除操作必须提供有效的key或keys参数")

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
