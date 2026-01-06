import logging
from typing import Dict, Any
from services.database.mongo_store import MongoDBService

logger = logging.getLogger(__name__)
mongodb_service = MongoDBService()

async def query_documents(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    查询文档
    
    Args:
        params: 包含查询参数的字典
            - cname (str): 集合名称 (必填)
            - ...: 其他查询参数
            
    Returns:
        Dict[str, Any]: 查询结果

    Example:
        GET /?module_name=services.database.data_service&method_name=query_documents&parameters={"cname": "users", "limit": 10}
        GET /?module_name=services.database.data_service&method_name=query_documents&parameters={"cname": "users", "fields": "name,email"}
    """
    cname = params.get('cname')
    if not cname:
        raise ValueError("Collection name (cname) is required")
    
    # 移除 cname，剩余的作为查询参数
    query_params = params.copy()
    if 'cname' in query_params:
        del query_params['cname']
    
    # 兼容旧参数：limit/page → 转换为分页参数，避免进入过滤条件
    try:
        if 'limit' in query_params and 'pageSize' not in query_params:
            query_params['pageSize'] = int(query_params.get('limit'))
        # 删除 limit，防止被当作过滤字段
        query_params.pop('limit', None)
    except (TypeError, ValueError):
        # 非法 limit 值则忽略
        query_params.pop('limit', None)
    
    try:
        if 'page' in query_params and 'pageNum' not in query_params:
            query_params['pageNum'] = int(query_params.get('page'))
        # 删除 page，防止被当作过滤字段
        query_params.pop('page', None)
    except (TypeError, ValueError):
        query_params.pop('page', None)
    
    return await mongodb_service.query_documents(
        cname=cname,
        query_params=query_params
    )

async def get_document_detail(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取文档详情
    
    Args:
        params: 参数字典
            - cname (str): 集合名称 (必填)
            - id (str): 文档 ID/Key (必填)
            
    Returns:
        Dict[str, Any]: 文档详情

    Example:
        GET /?module_name=services.database.data_service&method_name=get_document_detail&parameters={"cname": "users", "id": "12345"}
    """
    cname = params.get('cname')
    doc_id = params.get('id')
    
    if not cname or not doc_id:
        raise ValueError("cname and id are required")
        
    return await mongodb_service.get_document_detail(cname, doc_id)

async def create_document(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建文档
    
    Args:
        params: 参数字典
            - cname (str): 集合名称 (必填)
            - data (dict): 文档数据 (可选)
            - ...: 如果 data 不存在，使用 params 本身作为数据（除了 cname）
            
    Returns:
        Dict[str, Any]: 创建结果，包含新文档的 key

    Example:
        GET /?module_name=services.database.data_service&method_name=create_document&parameters={"cname": "users", "name": "test_user", "age": 25}
    """
    cname = params.get('cname')
    data = params.get('data')
    
    if not cname:
        raise ValueError("Collection name (cname) is required")
        
    if data is None:
        # 如果没有显式的 data 字段，使用 params 中除了 cname 以外的字段
        data = params.copy()
        del data['cname']
        
    return await mongodb_service.create_document(cname, data)

async def update_document(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    更新文档
    
    Args:
        params: 参数字典
            - cname (str): 集合名称 (必填)
            - data (dict): 更新数据 (必填)
            
    Returns:
        Dict[str, Any]: 更新结果，包含文档 key

    Example:
        GET /?module_name=services.database.data_service&method_name=update_document&parameters={"cname": "users", "data": {"key": "123", "name": "new_name"}}
    """
    cname = params.get('cname')
    data = params.get('data')
    
    if not cname:
        raise ValueError("Collection name (cname) is required")
        
    if data is None:
        data = params.copy()
        del data['cname']

    key = await mongodb_service.update_document(cname, data)
    return {'key': key}

async def delete_document(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    删除文档
    
    Args:
        params: 参数字典
            - cname (str): 集合名称 (必填)
            - id (str): 文档 ID/Key (必填)
            
    Returns:
        Dict[str, Any]: 删除结果 {"success": True}

    Example:
        GET /?module_name=services.database.data_service&method_name=delete_document&parameters={"cname": "users", "id": "12345"}
    """
    cname = params.get('cname')
    doc_id = params.get('id')
    
    if not cname or not doc_id:
        raise ValueError("cname and id are required")
        
    await mongodb_service.delete_document(cname, doc_id)
    return {'success': True}

