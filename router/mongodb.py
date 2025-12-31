from functools import wraps
from fastapi import APIRouter, Request, Body, HTTPException
from typing import Dict, Any, List, Optional
import re
import os
import shutil
from datetime import datetime, timedelta
import uuid
import logging
import hashlib
from bson import ObjectId
from Resp import RespOk
from pymongo import UpdateOne, ReturnDocument

from database import db
from router.utils import create_response, handle_error
from modules.services.fileStorageService import FileStorageService
from modules.services.syncService import SyncService
from modules.services.treeSyncService import TreeSyncService
from modules.utils.idConverter import (
    normalize_file_path_to_session_id,
    extract_project_id_from_file_path
)

router = APIRouter(
    prefix="/mongodb",
    tags=["mongodb"],
    responses={404: {"description": "Not found"}},
)

# 配置日志记录器
logger = logging.getLogger(__name__)

# 初始化文件存储和同步服务
_file_storage = None
_sync_service = None
_tree_sync_service = None

async def get_file_storage() -> FileStorageService:
    """获取文件存储服务实例（单例）"""
    global _file_storage
    if _file_storage is None:
        _file_storage = FileStorageService()
    return _file_storage

async def get_sync_service() -> SyncService:
    """获取同步服务实例（单例）"""
    global _sync_service
    if _sync_service is None:
        _sync_service = SyncService()
        await _sync_service.initialize()
    return _sync_service

async def get_tree_sync_service() -> TreeSyncService:
    """获取树同步服务实例（单例）"""
    global _tree_sync_service
    if _tree_sync_service is None:
        _tree_sync_service = TreeSyncService()
        await _tree_sync_service.initialize()
    return _tree_sync_service

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

def _generate_frontend_session_id(file_path: str, project_id: str) -> str:
    """
    生成前端格式的 Session ID（与前端 sessionSyncService.generateSessionId 逻辑一致）
    
    前端格式：${projectId}_${normalizedPath}（单下划线分隔）
    例如：knowledge_constructing_codereview_a
    
    Args:
        file_path: 文件路径
        project_id: 项目ID
    
    Returns:
        Session ID（前端格式）
    """
    if not file_path or not project_id:
        return f"{project_id}_{int(datetime.now().timestamp() * 1000)}"
    
    # 提取文件扩展名
    path_without_ext = file_path
    file_ext = ''
    if '.' in file_path:
        parts = file_path.rsplit('.', 1)
        path_without_ext = parts[0]
        file_ext = parts[1] if len(parts) > 1 else ''
    
    # 如果文件路径以项目ID开头，去除项目ID前缀（避免重复）
    if path_without_ext.startswith(f'{project_id}/'):
        path_without_ext = path_without_ext[len(project_id) + 1:]
    elif path_without_ext.startswith(project_id) and len(path_without_ext) > len(project_id):
        next_char = path_without_ext[len(project_id)]
        if next_char in ['/', '_']:
            path_without_ext = path_without_ext[len(project_id):].lstrip('/_')
    
    # 规范化文件路径：替换特殊字符为下划线，将斜杠替换为下划线
    normalized_path = re.sub(r'[^a-zA-Z0-9/]', '_', path_without_ext)
    normalized_path = re.sub(r'/+/', '_', normalized_path)  # 将斜杠替换为下划线
    normalized_path = re.sub(r'^_+|_+$', '', normalized_path)  # 移除首尾下划线
    normalized_path = re.sub(r'_+', '_', normalized_path)  # 合并连续下划线
    
    # 如果有扩展名，添加到末尾（用下划线分隔）
    if file_ext:
        normalized_path = f'{normalized_path}_{file_ext}'
    
    session_id = f'{project_id}_{normalized_path}'
    logger.debug(f"生成前端格式 Session ID: {file_path} -> {session_id}")
    return session_id

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

        # 对于 projectFiles 集合，从文件系统读取 content
        if cname == 'projectFiles':
            file_storage = await get_file_storage()
            for item in data:
                file_id = item.get('fileId') or item.get('id') or item.get('path')
                if file_id and file_storage.file_exists(file_id):
                    try:
                        content = file_storage.read_file_content(file_id)
                        item['content'] = content
                    except Exception as e:
                        logger.warning(f"从文件系统读取 content 失败: fileId={file_id}, 错误: {str(e)}")
                        item['content'] = ''  # 如果读取失败，设置为空字符串

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
    """
    获取MongoDB集合中的单条数据详情
    
    对于 projectFiles 集合，会从文件系统读取 content。
    """
    try:
        collection = db.mongodb.db[cname]
        document = await collection.find_one({'key': id}, {'_id': 0})

        if not document:
            raise ValueError(f"未找到ID为 {id} 的数据")

        # 对于 projectFiles 集合，从文件系统读取 content
        if cname == 'projectFiles':
            file_id = document.get('fileId') or document.get('id') or document.get('path')
            if file_id:
                file_storage = await get_file_storage()
                if file_storage.file_exists(file_id):
                    try:
                        content = file_storage.read_file_content(file_id)
                        document['content'] = content
                    except Exception as e:
                        logger.warning(f"从文件系统读取 content 失败: fileId={file_id}, 错误: {str(e)}")
                        document['content'] = ''  # 如果读取失败，设置为空字符串

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
    """
    创建MongoDB集合数据
    
    对于 projectFiles 集合，会将 content 字段写入文件系统，并同步到 Session。
    """
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

        # 对于 projectFiles 集合，处理文件存储
        content = None
        file_id = None
        project_id = None
        if cname == 'projectFiles':
            # 获取文件ID（fileId 或 id 或 path）
            file_id = data_copy.get('fileId') or data_copy.get('id') or data_copy.get('path')
            project_id = data_copy.get('projectId')
            content = data_copy.get('content', '')
            
            # 注意：文件写入由 sync_project_file_to_static 统一处理，这里不再单独写入
            # 这样可以确保文件路径格式一致（规范化后的路径）
            if file_id and content:
                # 计算内容哈希值（用于 MongoDB 存储）
                content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                data_copy['contentHash'] = content_hash
                # 不存储实际内容到 MongoDB（内容存储在文件系统）
                data_copy['content'] = ''
                logger.debug(f"ProjectFiles 内容准备同步到文件系统: fileId={file_id}")

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
            
            # 对于 projectFiles 集合，同步到 Session 和 static 目录
            if cname == 'projectFiles' and file_id and project_id:
                try:
                    sync_service = await get_sync_service()
                    sync_result = await sync_service.sync_project_file_to_session(
                        file_id=file_id,
                        project_id=project_id,
                        source_client="yiweb"
                    )
                    if sync_result.get("success"):
                        logger.info(f"ProjectFiles 已同步到 Session: fileId={file_id}")
                    else:
                        logger.warning(f"ProjectFiles 同步到 Session 失败: fileId={file_id}, 错误: {sync_result.get('error')}")
                except Exception as e:
                    logger.warning(f"同步 ProjectFiles 到 Session 失败: {str(e)}")
                
                # 同步到 static 目录
                try:
                    tree_sync_service = await get_tree_sync_service()
                    tree_sync_result = await tree_sync_service.sync_project_file_to_static(
                        file_id=file_id,
                        project_id=project_id,
                        content=content
                    )
                    if tree_sync_result.get("success"):
                        logger.info(f"ProjectFiles 已同步到 static 目录: fileId={file_id}")
                    else:
                        logger.warning(f"ProjectFiles 同步到 static 目录失败: fileId={file_id}, 错误: {tree_sync_result.get('error')}")
                except Exception as e:
                    logger.warning(f"同步 ProjectFiles 到 static 目录失败: {str(e)}")
            
            # 对于 projectTree 集合，同步到 static 目录
            if cname == 'projectTree':
                project_id = data_copy.get('projectId')
                if project_id:
                    try:
                        tree_sync_service = await get_tree_sync_service()
                        tree_sync_result = await tree_sync_service.sync_project_tree_to_static(project_id)
                        if tree_sync_result.get("success"):
                            logger.info(f"ProjectTree 已同步到 static 目录: projectId={project_id}")
                        else:
                            logger.warning(f"ProjectTree 同步到 static 目录失败: projectId={project_id}, 错误: {tree_sync_result.get('error')}")
                    except Exception as e:
                        logger.warning(f"同步 ProjectTree 到 static 目录失败: {str(e)}")
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
    """
    更新MongoDB集合数据
    
    对于 projectFiles 集合，会将 content 字段写入文件系统，并同步到 Session。
    """
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

        # 对于 projectFiles 集合，处理文件存储
        content = None
        file_id = None
        project_id = None
        if cname == 'projectFiles' and 'content' in data:
            # 先获取现有数据以确定 fileId 和 projectId
            existing_doc = await collection.find_one(query_filter)
            if existing_doc:
                file_id = existing_doc.get('fileId') or existing_doc.get('id') or existing_doc.get('path')
                project_id = existing_doc.get('projectId')
                content = data.get('content', '')
                
                if file_id and content:
                    # 写入文件系统
                    file_storage = await get_file_storage()
                    success = file_storage.write_file_content(file_id, content)
                    if success:
                        # 计算内容哈希值
                        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                        data['contentHash'] = content_hash
                        # 不存储实际内容到 MongoDB
                        data['content'] = ''
                        logger.info(f"ProjectFiles 内容已写入文件系统: fileId={file_id}")
                    else:
                        logger.warning(f"ProjectFiles 内容写入文件系统失败: fileId={file_id}")

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

        # 对于 projectFiles 集合，同步到 Session 和 static 目录
        if cname == 'projectFiles' and file_id and project_id:
            try:
                sync_service = await get_sync_service()
                sync_result = await sync_service.sync_project_file_to_session(
                    file_id=file_id,
                    project_id=project_id,
                    source_client="yiweb"
                )
                if sync_result.get("success"):
                    logger.info(f"ProjectFiles 已同步到 Session: fileId={file_id}")
                else:
                    logger.warning(f"ProjectFiles 同步到 Session 失败: fileId={file_id}, 错误: {sync_result.get('error')}")
            except Exception as e:
                logger.warning(f"同步 ProjectFiles 到 Session 失败: {str(e)}")
            
            # 同步到 static 目录
            if content:
                try:
                    tree_sync_service = await get_tree_sync_service()
                    tree_sync_result = await tree_sync_service.sync_project_file_to_static(
                        file_id=file_id,
                        project_id=project_id,
                        content=content
                    )
                    if tree_sync_result.get("success"):
                        logger.info(f"ProjectFiles 已同步到 static 目录: fileId={file_id}")
                    else:
                        logger.warning(f"ProjectFiles 同步到 static 目录失败: fileId={file_id}, 错误: {tree_sync_result.get('error')}")
                except Exception as e:
                    logger.warning(f"同步 ProjectFiles 到 static 目录失败: {str(e)}")
            
            # 如果更新了文件，同步整个项目树
            if content:
                try:
                    tree_sync_service = await get_tree_sync_service()
                    await tree_sync_service.sync_project_tree_to_static(project_id)
                except Exception as e:
                    logger.warning(f"同步项目树到 static 目录失败: {str(e)}")
        
        # 对于 projectTree 集合，同步到 static 目录
        if cname == 'projectTree':
            # 从更新后的文档中获取 projectId（因为更新请求可能不包含 projectId 字段）
            project_id = result.get('projectId') if result else data.get('projectId')
            if project_id:
                try:
                    tree_sync_service = await get_tree_sync_service()
                    tree_sync_result = await tree_sync_service.sync_project_tree_to_static(project_id)
                    if tree_sync_result.get("success"):
                        logger.info(f"ProjectTree 已同步到 static 目录: projectId={project_id}")
                    else:
                        logger.warning(f"ProjectTree 同步到 static 目录失败: projectId={project_id}, 错误: {tree_sync_result.get('error')}")
                except Exception as e:
                    logger.warning(f"同步 ProjectTree 到 static 目录失败: {str(e)}")
            else:
                logger.warning(f"ProjectTree 更新后无法获取 projectId，跳过同步到 static 目录")

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

            # 对于 projectFiles 集合，删除前获取文件信息以便同步删除 static 目录
            if cname == 'projectFiles':
                files_to_delete = await collection.find_many({'key': {'$in': keys_list}})
                project_ids = set()  # 收集所有涉及的项目ID
                tree_sync_service = None
                
                # 删除所有静态文件
                logger.info(f"[批量删除] 开始删除 {len(files_to_delete)} 个文件的静态文件")
                for file_doc in files_to_delete:
                    # 从多个位置获取 fileId：顶层和 data 字段
                    data_field = file_doc.get('data', {}) if isinstance(file_doc.get('data'), dict) else {}
                    file_id = (
                        file_doc.get('fileId') or 
                        file_doc.get('id') or 
                        file_doc.get('path') or
                        data_field.get('fileId') or
                        data_field.get('id') or
                        data_field.get('path')
                    )
                    project_id = file_doc.get('projectId') or data_field.get('projectId')
                    file_key = file_doc.get('key')
                    
                    if project_id:
                        project_ids.add(project_id)
                    
                    if file_id:
                        try:
                            if tree_sync_service is None:
                                tree_sync_service = await get_tree_sync_service()
                            # 检查是文件还是文件夹
                            file_path = tree_sync_service.file_storage.get_file_path(file_id)
                            is_folder = os.path.exists(file_path) and os.path.isdir(file_path)
                            
                            if is_folder:
                                logger.info(f"[批量删除] 检测到文件夹，递归删除静态文件夹: fileId={file_id}, key={file_key}")
                                result = await tree_sync_service.delete_project_folder_from_static(file_id)
                                if result.get('success'):
                                    deleted_count = result.get('deleted_count', 0)
                                    if result.get('skipped'):
                                        logger.info(f"[批量删除] 静态文件夹不存在（已跳过）: fileId={file_id}")
                                    else:
                                        logger.info(f"[批量删除] 成功递归删除静态文件夹: fileId={file_id}, 删除文件数={deleted_count}")
                                else:
                                    logger.error(f"[批量删除] 删除静态文件夹失败: fileId={file_id}, 错误: {result.get('error')}")
                            else:
                                logger.info(f"[批量删除] 删除静态文件: fileId={file_id}, key={file_key}")
                                # 传递 project_id 以便尝试多种路径格式
                                result = await tree_sync_service.delete_project_file_from_static(file_id, project_id)
                                if result.get('success'):
                                    if result.get('skipped'):
                                        logger.info(f"[批量删除] 静态文件不存在（已跳过）: fileId={file_id}")
                                    else:
                                        deleted_file_id = result.get('file_id', file_id)
                                        logger.info(f"[批量删除] 成功删除静态文件: fileId={deleted_file_id} (原始: {file_id})")
                                else:
                                    logger.error(f"[批量删除] 删除静态文件失败: fileId={file_id}, 错误: {result.get('error')}")
                            
                            # 删除对应的会话（如果是文件且找到了 projectId）
                            if project_id and not is_folder:
                                try:
                                    # 生成 sessionId（使用与前端一致的逻辑）
                                    session_id = _generate_frontend_session_id(file_id, project_id)
                                    logger.info(f"[批量删除] 准备删除会话: sessionId={session_id}, fileId={file_id}, projectId={project_id}")
                                    
                                    # 调用会话删除服务
                                    from modules.services.sessionService import SessionService
                                    session_service = SessionService()
                                    await session_service.initialize()
                                    success = await session_service.delete_session(session_id)
                                    
                                    if success:
                                        logger.info(f"[批量删除] ✓ 成功删除会话: sessionId={session_id}, fileId={file_id}")
                                    else:
                                        logger.warning(f"[批量删除] ✗ 会话删除失败或不存在: sessionId={session_id}, fileId={file_id}")
                                except Exception as e:
                                    logger.warning(f"[批量删除] ✗ 删除会话异常（已忽略）: fileId={file_id}, projectId={project_id}, 错误: {str(e)}")
                        except Exception as e:
                            logger.error(f"[批量删除] 删除静态文件异常: fileId={file_id}, 错误: {str(e)}", exc_info=True)
                    else:
                        logger.warning(f"[批量删除] 无法获取 fileId，跳过删除静态文件: key={file_key}")
                
                # 所有文件删除后，同步一次项目树（如果有项目ID）
                if project_ids and tree_sync_service:
                    logger.info(f"[批量删除] 开始同步 {len(project_ids)} 个项目树")
                    for project_id in project_ids:
                        try:
                            logger.info(f"[批量删除] 同步项目树: projectId={project_id}")
                            await tree_sync_service.sync_project_tree_to_static(project_id)
                            logger.info(f"[批量删除] 同步项目树成功: projectId={project_id}")
                        except Exception as e:
                            logger.warning(f"[批量删除] 同步项目树失败: projectId={project_id}, 错误: {str(e)}")
            
            # 对于 projectTree 集合，删除前获取项目ID以便同步删除 static 目录
            if cname == 'projectTree':
                trees_to_delete = await collection.find_many({'key': {'$in': keys_list}})
                for tree_doc in trees_to_delete:
                    project_id = tree_doc.get('projectId')
                    if project_id:
                        try:
                            tree_sync_service = await get_tree_sync_service()
                            # 删除整个项目的 static 目录
                            project_static_dir = tree_sync_service.file_storage.get_file_path(project_id)
                            if os.path.exists(project_static_dir):
                                shutil.rmtree(project_static_dir)
                                logger.info(f"已删除项目 static 目录: projectId={project_id}")
                        except Exception as e:
                            logger.warning(f"删除项目 static 目录失败: projectId={project_id}, 错误: {str(e)}")

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
            # 对于 projectFiles 集合，删除前获取文件信息以便同步删除 static 目录
            if cname == 'projectFiles':
                file_doc = await collection.find_one({'key': key})
                file_id = None
                project_id = None
                
                if file_doc:
                    # 从多个位置获取 fileId：顶层和 data 字段
                    data_field = file_doc.get('data', {}) if isinstance(file_doc.get('data'), dict) else {}
                    file_id = (
                        file_doc.get('fileId') or 
                        file_doc.get('id') or 
                        file_doc.get('path') or
                        data_field.get('fileId') or
                        data_field.get('id') or
                        data_field.get('path')
                    )
                    project_id = file_doc.get('projectId') or data_field.get('projectId')
                    
                    # 添加详细的日志输出，帮助调试
                    logger.info(f"[删除] 找到文件文档: key={key}, fileId={file_id}, projectId={project_id}")
                    logger.debug(f"[删除] 文档结构: fileId={file_id}, projectId={project_id}, fileId字段={file_doc.get('fileId')}, id字段={file_doc.get('id')}, path字段={file_doc.get('path')}")
                    
                    # 注意：不在这里规范化 fileId，让 delete_project_file_from_static 使用统一的规范化逻辑
                else:
                    logger.warning(f"[删除] 未找到文件文档: key={key}")
                    # 即使找不到文档，也尝试通过 key 查找可能的文件路径
                    # 这里可以尝试从其他集合或缓存中查找
                
                # 删除静态文件（如果找到了 fileId）
                if file_id:
                    logger.info(f"[删除] 准备删除静态文件: fileId={file_id}")
                    try:
                        tree_sync_service = await get_tree_sync_service()
                        # 检查是文件还是文件夹
                        file_path = tree_sync_service.file_storage.get_file_path(file_id)
                        logger.debug(f"[删除] 静态文件路径: {file_path}")
                        is_folder = os.path.exists(file_path) and os.path.isdir(file_path)
                        
                        if is_folder:
                            logger.info(f"[删除] 检测到文件夹，开始递归删除静态文件夹: fileId={file_id}, path={file_path}")
                            result = await tree_sync_service.delete_project_folder_from_static(file_id)
                            if result.get('success'):
                                deleted_count = result.get('deleted_count', 0)
                                if result.get('skipped'):
                                    logger.info(f"[删除] 静态文件夹不存在（已跳过）: fileId={file_id}")
                                else:
                                    logger.info(f"[删除] 成功递归删除静态文件夹: fileId={file_id}, 删除文件数={deleted_count}")
                            else:
                                logger.error(f"[删除] 删除静态文件夹失败: fileId={file_id}, 错误: {result.get('error')}")
                                # 即使删除静态文件夹失败，也继续删除 MongoDB 记录
                        else:
                            logger.info(f"[删除] 开始删除静态文件: fileId={file_id}, path={file_path}")
                            # 传递 project_id 以便尝试多种路径格式
                            result = await tree_sync_service.delete_project_file_from_static(file_id, project_id)
                            if result.get('success'):
                                if result.get('skipped'):
                                    logger.info(f"[删除] 静态文件不存在（已跳过）: fileId={file_id}, path={file_path}")
                                else:
                                    deleted_file_id = result.get('file_id', file_id)
                                    logger.info(f"[删除] 成功删除静态文件: fileId={deleted_file_id} (原始: {file_id}), path={file_path}")
                            else:
                                logger.error(f"[删除] 删除静态文件失败: fileId={file_id}, path={file_path}, 错误: {result.get('error')}")
                                # 即使删除静态文件失败，也继续删除 MongoDB 记录
                    except Exception as e:
                        logger.error(f"[删除] 删除静态文件异常: fileId={file_id}, 错误: {str(e)}", exc_info=True)
                        # 即使删除静态文件异常，也继续删除 MongoDB 记录
                    
                    # 删除对应的会话（如果是文件且找到了 projectId）
                    if project_id and not is_folder:
                        try:
                            # 生成 sessionId（使用与前端一致的逻辑）
                            # 前端格式：${projectId}_${normalizedPath}（单下划线分隔）
                            session_id = _generate_frontend_session_id(file_id, project_id)
                            logger.info(f"[删除] 准备删除会话: sessionId={session_id}, fileId={file_id}, projectId={project_id}")
                            
                            # 调用会话删除服务
                            from modules.services.sessionService import SessionService
                            session_service = SessionService()
                            await session_service.initialize()
                            success = await session_service.delete_session(session_id)
                            
                            if success:
                                logger.info(f"[删除] ✓ 成功删除会话: sessionId={session_id}, fileId={file_id}")
                            else:
                                logger.warning(f"[删除] ✗ 会话删除失败或不存在: sessionId={session_id}, fileId={file_id}")
                        except Exception as e:
                            logger.warning(f"[删除] ✗ 删除会话异常（已忽略）: fileId={file_id}, projectId={project_id}, 错误: {str(e)}")
                            # 即使删除会话失败，也继续删除 MongoDB 记录
                else:
                    logger.warning(f"[删除] 无法获取 fileId，无法删除静态文件: key={key}, 文档: {file_doc if file_doc else '未找到'}")
                
                # 同步整个项目树（如果找到了 projectId）
                if project_id:
                    try:
                        tree_sync_service = await get_tree_sync_service()
                        logger.info(f"[删除] 开始同步项目树: projectId={project_id}")
                        await tree_sync_service.sync_project_tree_to_static(project_id)
                        logger.info(f"[删除] 同步项目树成功: projectId={project_id}")
                    except Exception as e:
                        logger.warning(f"[删除] 同步项目树失败: projectId={project_id}, 错误: {str(e)}")
            
            # 对于 projectTree 集合，删除前获取项目ID以便同步删除 static 目录
            if cname == 'projectTree':
                tree_doc = await collection.find_one({'key': key})
                if tree_doc:
                    project_id = tree_doc.get('projectId')
                    if project_id:
                        try:
                            tree_sync_service = await get_tree_sync_service()
                            # 删除整个项目的 static 目录
                            project_static_dir = tree_sync_service.file_storage.get_file_path(project_id)
                            if os.path.exists(project_static_dir):
                                shutil.rmtree(project_static_dir)
                                logger.info(f"已删除项目 static 目录: projectId={project_id}")
                        except Exception as e:
                            logger.warning(f"删除项目 static 目录失败: projectId={project_id}, 错误: {str(e)}")
            
            # 优先使用key字段
            # 注意：对于 projectFiles，静态文件已经在上面删除了
            result = await collection.delete_one({'key': key})
            if result.deleted_count == 0:
                raise ValueError(f"未找到key为 {key} 的数据")
            
            # 对于 projectFiles，记录删除结果
            if cname == 'projectFiles':
                logger.info(f"[删除] MongoDB 记录删除成功: key={key}, deleted_count={result.deleted_count}")
            
            return RespOk(data={"deleted_count": result.deleted_count})
        
        elif link:
            # 兼容使用link字段替换key字段
            result = await collection.delete_one({'link': link})
            if result.deleted_count == 0:
                raise ValueError(f"未找到link为 {link} 的数据")
            return RespOk(data={"deleted_count": result.deleted_count})
        
        elif query_params.get('fileId'):
            # 支持通过 fileId 删除（主要用于 projectFiles 集合）
            file_id = query_params.get('fileId')
            if cname == 'projectFiles':
                # 先查找文件，获取文件信息以便删除静态文件
                # 同时检查顶层和 data 字段
                file_doc = await collection.find_one({
                    '$or': [
                        {'fileId': file_id},
                        {'id': file_id},
                        {'path': file_id},
                        {'data.fileId': file_id},
                        {'data.id': file_id},
                        {'data.path': file_id}
                    ]
                })
                
                project_id = None
                doc_key = None
                target_file_id = file_id  # 默认使用查询的 fileId
                
                if file_doc:
                    # 从多个位置获取 fileId：顶层和 data 字段
                    data_field = file_doc.get('data', {}) if isinstance(file_doc.get('data'), dict) else {}
                    doc_file_id = (
                        file_doc.get('fileId') or 
                        file_doc.get('id') or 
                        file_doc.get('path') or
                        data_field.get('fileId') or
                        data_field.get('id') or
                        data_field.get('path')
                    )
                    project_id = file_doc.get('projectId') or data_field.get('projectId')
                    doc_key = file_doc.get('key')
                    
                    # 优先使用文档中的 fileId
                    if doc_file_id:
                        target_file_id = doc_file_id
                    
                    logger.info(f"[删除] 通过 fileId 找到文件: fileId={file_id}, doc_fileId={doc_file_id}, target_fileId={target_file_id}, projectId={project_id}")
                else:
                    logger.warning(f"[删除] 通过 fileId 未找到文件文档，将直接使用 fileId 删除静态文件: fileId={file_id}")
                
                # 删除静态文件
                if target_file_id:
                    try:
                        tree_sync_service = await get_tree_sync_service()
                        # 检查是文件还是文件夹
                        file_path = tree_sync_service.file_storage.get_file_path(target_file_id)
                        is_folder = os.path.exists(file_path) and os.path.isdir(file_path)
                        
                        if is_folder:
                            logger.info(f"[删除] 检测到文件夹，开始递归删除静态文件夹: fileId={target_file_id}")
                            result = await tree_sync_service.delete_project_folder_from_static(target_file_id)
                            if result.get('success'):
                                deleted_count = result.get('deleted_count', 0)
                                if result.get('skipped'):
                                    logger.info(f"[删除] 静态文件夹不存在（已跳过）: fileId={target_file_id}")
                                else:
                                    logger.info(f"[删除] 成功递归删除静态文件夹: fileId={target_file_id}, 删除文件数={deleted_count}")
                            else:
                                logger.error(f"[删除] 删除静态文件夹失败: fileId={target_file_id}, 错误: {result.get('error')}")
                                # 即使删除静态文件夹失败，也继续删除 MongoDB 记录
                        else:
                            logger.info(f"[删除] 开始删除静态文件: fileId={target_file_id}")
                            # 传递 project_id 以便尝试多种路径格式
                            result = await tree_sync_service.delete_project_file_from_static(target_file_id, project_id)
                            if result.get('success'):
                                if result.get('skipped'):
                                    logger.info(f"[删除] 静态文件不存在（已跳过）: fileId={target_file_id}")
                                else:
                                    deleted_file_id = result.get('file_id', target_file_id)
                                    logger.info(f"[删除] 成功删除静态文件: fileId={deleted_file_id} (原始: {target_file_id})")
                            else:
                                logger.error(f"[删除] 删除静态文件失败: fileId={target_file_id}, 错误: {result.get('error')}")
                                # 即使删除静态文件失败，也继续删除 MongoDB 记录
                        
                        # 删除对应的会话（如果是文件且找到了 projectId）
                        if project_id and not is_folder:
                            try:
                                # 生成 sessionId（使用与前端一致的逻辑）
                                session_id = _generate_frontend_session_id(target_file_id, project_id)
                                logger.info(f"[删除] 准备删除会话: sessionId={session_id}, fileId={target_file_id}, projectId={project_id}")
                                
                                # 调用会话删除服务
                                from modules.services.sessionService import SessionService
                                session_service = SessionService()
                                await session_service.initialize()
                                success = await session_service.delete_session(session_id)
                                
                                if success:
                                    logger.info(f"[删除] ✓ 成功删除会话: sessionId={session_id}, fileId={target_file_id}")
                                else:
                                    logger.warning(f"[删除] ✗ 会话删除失败或不存在: sessionId={session_id}, fileId={target_file_id}")
                            except Exception as e:
                                logger.warning(f"[删除] ✗ 删除会话异常（已忽略）: fileId={target_file_id}, projectId={project_id}, 错误: {str(e)}")
                    except Exception as e:
                        logger.error(f"[删除] 删除静态文件异常: fileId={target_file_id}, 错误: {str(e)}", exc_info=True)
                        # 即使删除静态文件异常，也继续删除 MongoDB 记录
                
                # 同步整个项目树
                if project_id:
                    try:
                        tree_sync_service = await get_tree_sync_service()
                        logger.info(f"[删除] 开始同步项目树: projectId={project_id}")
                        await tree_sync_service.sync_project_tree_to_static(project_id)
                        logger.info(f"[删除] 同步项目树成功: projectId={project_id}")
                    except Exception as e:
                        logger.warning(f"[删除] 同步项目树失败: projectId={project_id}, 错误: {str(e)}")
                    
                    # 使用 key 删除（如果存在），否则使用 fileId/id/path 删除
                    if doc_key:
                        result = await collection.delete_one({'key': doc_key})
                    else:
                        result = await collection.delete_one({
                            '$or': [
                                {'fileId': file_id},
                                {'id': file_id},
                                {'path': file_id}
                            ]
                        })
                    
                    if result.deleted_count == 0:
                        raise ValueError(f"未找到fileId为 {file_id} 的数据")
                    return RespOk(data={"deleted_count": result.deleted_count})
                else:
                    raise ValueError(f"未找到fileId为 {file_id} 的数据")
            else:
                # 非 projectFiles 集合，直接通过 fileId 删除
                result = await collection.delete_one({
                    '$or': [
                        {'fileId': file_id},
                        {'id': file_id},
                        {'path': file_id}
                    ]
                })
                if result.deleted_count == 0:
                    raise ValueError(f"未找到fileId为 {file_id} 的数据")
                return RespOk(data={"deleted_count": result.deleted_count})

        else:
            raise ValueError("删除操作必须提供有效的key、link、keys、links或fileId参数")

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


