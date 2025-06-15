from functools import wraps
from fastapi import APIRouter, Request, Body # type: ignore
from typing import Dict, Any
import re
from datetime import datetime
import uuid
import logging
from bson import ObjectId # type: ignore
from Resp import RespOk
from pymongo import UpdateOne, ReturnDocument # type: ignore

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

def create_response(code: int, message: str, data: Any = None) -> dict:
    """统一的响应格式"""
    return {
        "code": code,
        "message": message,
        "data": data
    }

def handle_error(e: Exception, status_code: int = 500) -> dict:
    """统一的错误处理"""
    logger.error(f"Error occurred: {str(e)}")
    return create_response(
        code=status_code,
        message=str(e),
        data=None
    ) 

def build_filter(query_params: Dict[str, Any]) -> Dict[str, Any]:
    filter_dict = {}
    
    for key, value in query_params.items():
        if not value:  # 跳过空值
            continue
            
        if isinstance(value, list):
            if not value:  # 跳过空列表
                continue
                
            if len(value) == 2:  # 范围查询
                start, end = value
                if is_valid_date(start) and is_valid_date(end):
                    filter_dict[key] = {'$gte': start, '$lt': end}
                elif is_number(start) or is_number(end):
                    start_val = 0 if not is_number(start) else float(start)
                    end_val = 9223372036854775806 if not is_number(end) else float(end)
                    filter_dict[key] = {'$gte': start_val, '$lt': end_val}
            else:  # 多值查询
                filter_dict[key] = {'$in': value}
                
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

@router.get("/")
@ensure_initialized()
async def query(request: Request):
    try:
        query_params = dict(request.query_params)
        
        # 验证必要参数
        if 'cname' not in query_params:
            raise ValueError("缺少必要参数: cname")
            
        cname = query_params.pop('cname')
        
        # 验证分页参数
        try:
            page_num = max(1, int(query_params.pop('pageNum', 1)))
            page_size = min(999999999, max(1, int(query_params.pop('pageSize', 999999999))))
        except ValueError:
            raise ValueError("分页参数必须是有效的整数")
            
        # 验证排序参数
        sort_param = query_params.pop('orderBy', 'order')
        sort_order = -1 if query_params.pop('orderType', 'asc').lower() == 'desc' else 1
        
        # 构建查询条件
        filter_dict = build_filter(query_params)
        projection = {'_id': 0}
        
        # 执行查询
        collection = db.mongodb.db[cname]
        
        # 设置排序规则：如果指定了排序字段，则优先使用该字段
        sort_list = []
        if sort_param == 'order':
            # 默认按order字段升序排列
            sort_list.append(('order', 1))
        else:
            # 使用指定的排序字段和顺序
            sort_list.append((sort_param, sort_order))
            
        # 添加次要排序条件
        if sort_param != 'updatedTime':
            sort_list.append(('updatedTime', -1))
        if sort_param != 'createdTime':
            sort_list.append(('createdTime', -1))
        
        # 执行查询
        cursor = collection.find(filter_dict, projection) \
            .sort(sort_list) \
            .skip((page_num - 1) * page_size) \
            .limit(page_size)
        
        # 获取数据
        data = []
        async for doc in cursor:
            data.append(doc)
            
        # 获取总数
        total = await collection.count_documents(filter_dict)
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size
        
        # 返回结果
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
        return handle_error(e)
    except Exception as e:
        logger.error(f"查询数据失败: {str(e)}", exc_info=True)
        return handle_error(e)

@router.get("/detail")
@ensure_initialized()
async def get_detail(cname: str, id: str):
    """获取MongoDB集合中的单条数据详情"""
    try:
        collection = db.mongodb.db[cname]
        filter_dict = {'key': id}
        projection = {'_id': 0}
        
        document = await collection.find_one(filter_dict, projection)
        if not document:
            raise ValueError(f"未找到ID为 {id} 的数据")
            
        return RespOk(data=document)
    except ValueError as e:
        logger.warning(f"获取详情失败: {str(e)}")
        return handle_error(e)
    except Exception as e:
        logger.error(f"获取详情失败: {str(e)}", exc_info=True)
        return handle_error(e)

@router.post("/")
@ensure_initialized()
async def create(request: Request, data: Dict[str, Any] = Body(...)):
    try:
        # 获取集合名称
        query_params = dict(request.query_params)
        cname = query_params.get('cname')
        
        if not cname:
            if 'cname' in data:
                cname = data.pop('cname')
            else:
                raise ValueError("必须提供集合名称(cname)")
                
        if not data:
            raise ValueError("创建数据不能为空")
            
        collection = db.mongodb.db[cname]
        
        # 记录请求数据
        logger.info(f"创建数据请求 - 集合: {cname}, 数据: {data}")
        
        # 准备数据
        data_copy = {}
        for k, v in data.items():
            if isinstance(v, ObjectId):
                data_copy[k] = str(v)
            else:
                data_copy[k] = v
                
        # 生成唯一标识和创建时间
        data_copy['key'] = str(uuid.uuid4())
        data_copy['createdTime'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        data_copy['updatedTime'] = data_copy['createdTime']
        
        # 设置默认排序值（获取当前最大order值并加1）
        try:
            max_order_doc = await collection.find_one(sort=[("order", -1)], projection={"order": 1})
            max_order = max_order_doc.get("order", 0) if max_order_doc else 0
            data_copy['order'] = max_order + 1
        except Exception as e:
            logger.error(f"获取最大排序值失败: {str(e)}")
            data_copy['order'] = 1
        
        # 插入数据
        try:
            result = await collection.insert_one(data_copy)
            logger.info(f"数据创建成功 - 集合: {cname}, ID: {result.inserted_id}")
        except Exception as e:
            logger.error(f"数据插入失败: {str(e)}")
            raise ValueError(f"数据插入失败: {str(e)}")
        
        # 返回结果
        return RespOk(data={'key': data_copy['key']})
    except ValueError as e:
        logger.warning(f"数据验证失败: {str(e)}")
        return handle_error(e)
    except Exception as e:
        logger.error(f"创建数据失败: {str(e)}", exc_info=True)
        return handle_error(e)

@router.put("/")
@ensure_initialized()
async def update(request: Request, data: Dict[str, Any] = Body(...)):
    try:
        # 获取集合名称
        query_params = dict(request.query_params)
        cname = query_params.get('cname')
        
        if not cname:
            if 'cname' in data:
                cname = data.pop('cname')
            else:
                raise ValueError("必须提供集合名称(cname)")
            
        # 验证key字段
        if 'key' not in data or not data['key']:
            raise ValueError("更新数据时必须提供key字段")
            
        key = data.get('key')
        if len(data) <= 1:  # 只有key字段
            raise ValueError("更新数据不能为空")
            
        collection = db.mongodb.db[cname]
            
        # 准备更新
        filter_dict = {'key': key}
        data['updatedTime'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # 执行更新
        result = await collection.find_one_and_update(
            filter_dict, 
            {"$set": data},
            return_document=ReturnDocument.AFTER
        )
        
        # 验证结果
        if not result:
            raise ValueError(f"未找到key为 {key} 的数据")
            
        return RespOk(data={"key": key, "updated": True})
    except ValueError as e:
        logger.warning(f"数据验证失败: {str(e)}")
        return handle_error(e)
    except Exception as e:
        logger.error(f"更新数据失败: {str(e)}", exc_info=True)
        return handle_error(e)

@router.delete("/")
@ensure_initialized()
async def delete(request: Request):
    """删除MongoDB集合中的数据"""
    try:
        # 获取集合名称和参数
        query_params = dict(request.query_params)
        cname = query_params.get('cname')
        key = query_params.get('key')
        keys_str = query_params.get('keys')
        
        if not cname:
            raise ValueError("必须提供集合名称(cname)")
            
        collection = db.mongodb.db[cname]
        
        # 处理批量删除
        if keys_str:
            try:
                # 尝试将逗号分隔的字符串转换为列表
                keys_list = keys_str.split(',')
                if keys_list:
                    filter_dict = {'key': {'$in': keys_list}}
                    result = await collection.delete_many(filter_dict)
                    return RespOk(data={"deleted_count": result.deleted_count})
                else:
                    raise ValueError("keys参数不能为空")
            except Exception as e:
                raise ValueError(f"处理keys参数时出错: {str(e)}")
        
        # 处理单个删除
        elif key:
            filter_dict = {'key': key}
            result = await collection.delete_one(filter_dict)
            if result.deleted_count == 0:
                raise ValueError(f"未找到key为 {key} 的数据")
            return RespOk(data={"deleted_count": result.deleted_count})
        
        else:
            raise ValueError("删除操作必须提供有效的key或keys参数")
            
    except ValueError as e:
        logger.warning(f"删除数据验证失败: {str(e)}")
        return handle_error(e)
    except Exception as e:
        logger.error(f"删除数据失败: {str(e)}", exc_info=True)
        return handle_error(e)

@router.put("/batch-order")
@ensure_initialized()
async def batch_order(request: Request, data: Dict[str, Any] = Body(...)):
    try:
        # 获取集合名称
        query_params = dict(request.query_params)
        cname = query_params.get('cname')
        
        if not cname:
            if 'cname' in data:
                cname = data.pop('cname')
            else:
                raise ValueError("必须提供集合名称(cname)")
        
        # 验证必要参数
        if 'orders' not in data or not isinstance(data['orders'], list) or not data['orders']:
            raise ValueError("必须提供有效的排序项列表(orders)")
            
        orders = data['orders']
        
        # 验证每个排序项
        for item in orders:
            if 'key' not in item or not item['key']:
                raise ValueError("每个排序项必须提供有效的key")
            if 'order' not in item:
                raise ValueError("每个排序项必须提供有效的order值")
                
        collection = db.mongodb.db[cname]
        
        # 批量更新操作
        update_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        operations = []
        
        for item in orders:
            key = item['key']
            order_value = item['order']
            
            operations.append(
                UpdateOne(
                    {'key': key},
                    {
                        '$set': {
                            'order': order_value,
                            'updatedTime': update_time
                        }
                    }
                )
            )
        
        # 执行批量更新
        if operations:
            result = await collection.bulk_write(operations)
            
            # 返回结果
            return RespOk(data={
                "updated_count": result.modified_count,
                "total_count": len(operations)
            })
        else:
            return RespOk(data={"updated_count": 0, "total_count": 0})
            
    except ValueError as e:
        logger.warning(f"批量排序数据验证失败: {str(e)}")
        return handle_error(e)
    except Exception as e:
        logger.error(f"批量排序失败: {str(e)}", exc_info=True)
        return handle_error(e)