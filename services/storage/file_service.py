import logging
import os
import base64
from typing import Dict, Any, List
from fastapi import UploadFile
from services.storage import oss_client as oss_service

logger = logging.getLogger(__name__)

async def delete_file(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    删除 OSS 文件
    
    Args:
        params: 参数字典
            - osspath (str): 文件路径 (兼容旧参数)
            - object_name (str): 文件对象名 (新参数)
            
    Returns:
        Dict[str, Any]: 操作结果
            - success (bool): 是否成功
            - object_name (str): 删除的对象名
            
    Raises:
        ValueError: 未提供 object_name 或 osspath

    Example:
        GET /?module_name=services.storage.file_service&method_name=delete_file&parameters={"object_name": "images/test.jpg"}
    """
    object_name = params.get('object_name') or params.get('osspath')
    if not object_name:
        raise ValueError("object_name or osspath is required")
        
    await oss_service.delete_oss_file(object_name)
    return {"success": True, "object_name": object_name}

async def list_files(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    列出文件
    
    Args:
        params: 参数字典
            - directory (str, optional): 目录前缀
            - tags (str, optional): 标签过滤，逗号分隔
            
    Returns:
        List[Dict[str, Any]]: 文件列表

    Example:
        GET /?module_name=services.storage.file_service&method_name=list_files&parameters={"directory": "images/", "tags": "public"}
    """
    directory = params.get('directory')
    tags = params.get('tags')
    return await oss_service.list_files(directory, tags)

async def set_tags(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    设置标签
    
    Args:
        params: 参数字典
            - object_name (str): 文件对象名
            - tags (List[str]): 标签列表
            
    Returns:
        Dict[str, Any]: 更新后的标签信息
        
    Raises:
        ValueError: object_name 未提供

    Example:
        GET /?module_name=services.storage.file_service&method_name=set_tags&parameters={"object_name": "images/test.jpg", "tags": ["vacation", "2023"]}
    """
    object_name = params.get('object_name')
    tags = params.get('tags', [])
    
    if not object_name:
        raise ValueError("object_name is required")
        
    return await oss_service.set_file_tags(object_name, tags)

async def get_tags(params: Dict[str, Any]) -> List[str]:
    """
    获取标签
    Params:
        object_name (str): 文件对象名
        
    Example:
        GET /?module_name=services.storage.file_service&method_name=get_tags&parameters={"object_name": "images/test.jpg"}
    """
    object_name = params.get('object_name')
    if not object_name:
        raise ValueError("object_name is required")
        
    return await oss_service.get_file_tags(object_name)

async def update_info(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    更新文件信息
    Params:
        object_name (str): 文件对象名
        title (str, optional): 标题
        description (str, optional): 描述
    """
    object_name = params.get('object_name')
    title = params.get('title')
    description = params.get('description')
    
    if not object_name:
        raise ValueError("object_name is required")
        
    return await oss_service.update_file_info(object_name, title, description)

async def get_info(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取文件信息
    
    Args:
        params: 参数字典
            - object_name (str): 文件对象名
            
    Returns:
        Dict[str, Any]: 文件信息字典
        
    Raises:
        ValueError: object_name 未提供

    Example:
        GET /?module_name=services.storage.file_service&method_name=get_info&parameters={"object_name": "images/test.jpg"}
    """
    object_name = params.get('object_name')
    if not object_name:
        raise ValueError("object_name is required")
        
    return await oss_service.get_file_info(object_name)

# 注意：Upload 功能在此模式下较难支持，除非传入 Base64 或文件路径
# 如果必须支持，可以添加 upload_from_path 或 upload_base64

