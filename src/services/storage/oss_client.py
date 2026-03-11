"""OSS 存储服务封装
- 提供文件上传/删除、标签管理、文件信息维护与列表查询
"""
import os
import oss2
import logging
from typing import Optional, List, Dict, Any
from fastapi import UploadFile, HTTPException
from datetime import datetime, timezone
from core.config import settings
from core.database import db

logger = logging.getLogger(__name__)

class OSSConfig:
    """从配置加载 OSS 连接参数"""
    def __init__(self):
        """初始化 OSS 配置"""
        self.access_key_id = settings.oss_access_key
        self.access_key_secret = settings.oss_secret_key
        self.endpoint = settings.oss_endpoint
        self.bucket_name = settings.oss_bucket

        if not all([self.access_key_id, self.access_key_secret, self.endpoint, self.bucket_name]):
            logger.warning("OSS config incomplete.")

def get_bucket(config: OSSConfig) -> oss2.Bucket:
    """
    构建 Bucket 客户端
    
    Args:
        config: OSS 配置对象
        
    Returns:
        oss2.Bucket: OSS Bucket 实例
    """
    auth = oss2.Auth(config.access_key_id, config.access_key_secret)
    return oss2.Bucket(auth, config.endpoint, config.bucket_name)

def build_oss_url(bucket_name: str, endpoint: str, object_key: str) -> str:
    """
    根据 bucket、endpoint 与对象名生成可访问 URL
    
    Args:
        bucket_name: Bucket 名称
        endpoint: 接入点域名
        object_key: 对象键名
        
    Returns:
        str: 完整的 HTTPS URL
    """
    clean_endpoint = endpoint.replace('http://', '').replace('https://', '')
    return f"https://{bucket_name}.{clean_endpoint}/{object_key}"

async def upload_file_to_oss(
    file: UploadFile,
    directory: Optional[str] = None
) -> dict:
    """上传文件到 OSS（参数校验、大小限制、返回可访问地址）"""
    config = OSSConfig()
    bucket = get_bucket(config)
    
    ALLOWED_EXTENSIONS = set(ext.lower() for ext in settings.oss_allowed_extensions)
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")

    content = await file.read()
    if len(content) > settings.oss_max_file_size:
        raise HTTPException(status_code=400, detail=f"File too large")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    object_name = f"{directory + '/' if directory else ''}{timestamp}{file_ext}"

    bucket.put_object(object_name, content)
    file_url = build_oss_url(config.bucket_name, config.endpoint, object_name)
    
    return {
        "url": file_url,
        "filename": file.filename,
        "object_name": object_name
    }

async def upload_bytes_to_oss(
    content: bytes,
    filename: str,
    directory: Optional[str] = None
) -> dict:
    config = OSSConfig()
    bucket = get_bucket(config)

    ALLOWED_EXTENSIONS = set(ext.lower() for ext in settings.oss_allowed_extensions)
    safe_filename = (filename or "").strip() or "image.png"
    file_ext = os.path.splitext(safe_filename)[1].lower() or ".png"
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")

    if len(content) > settings.oss_max_file_size:
        raise HTTPException(status_code=400, detail="File too large")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    object_name = f"{directory + '/' if directory else ''}{timestamp}{file_ext}"

    bucket.put_object(object_name, content)
    file_url = build_oss_url(config.bucket_name, config.endpoint, object_name)

    return {
        "url": file_url,
        "filename": safe_filename,
        "object_name": object_name
    }

async def delete_oss_file(object_name: str):
    """
    删除 OSS 文件，并清理相关标签与信息
    
    Args:
        object_name: 文件对象名
        
    Returns:
        str: 删除的对象名
        
    Raises:
        HTTPException: 文件不存在

    Example:
        GET /?module_name=services.storage.oss_client&method_name=delete_oss_file&parameters={"object_name": "images/test.jpg"}
    """
    config = OSSConfig()
    bucket = get_bucket(config)
    
    if not bucket.object_exists(object_name):
        raise HTTPException(status_code=404, detail="File not found")
        
    bucket.delete_object(object_name)
    
    await db.initialize()
    try:
        await db.delete_one(settings.collection_oss_file_tags, {"object_name": object_name})
        await db.delete_one(settings.collection_oss_file_info, {"object_name": object_name})
    except Exception as e:
        logger.warning(f"Cleanup DB failed for {object_name}: {e}")
        
    return object_name

async def set_file_tags(object_name: str, tags: List[str]) -> Dict[str, Any]:
    """
    设置文件标签（去重、幂等更新）
    
    Args:
        object_name: 文件对象名
        tags: 标签列表
        
    Returns:
        Dict[str, Any]: 更新后的标签信息
        
    Raises:
        ValueError: 文件对象名为空

    Example:
        GET /?module_name=services.storage.oss_client&method_name=set_file_tags&parameters={"object_name": "images/test.jpg", "tags": ["vacation", "2023"]}
    """
    if not object_name:
        raise ValueError("文件对象名不能为空")

    tags = [tag.strip() for tag in tags if tag.strip()]
    tags = list(set(tags))

    await db.initialize()
    collection = db.db[settings.collection_oss_file_tags]

    await collection.update_one(
        {"object_name": object_name},
        {
            "$set": {
                "object_name": object_name,
                "tags": tags,
                "updatedTime": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            }
        },
        upsert=True
    )
    return {"object_name": object_name, "tags": tags}

async def get_file_tags(object_name: str) -> List[str]:
    """
    获取文件标签列表
    
    Example:
        GET /?module_name=services.storage.oss_client&method_name=get_file_tags&parameters={"object_name": "images/test.jpg"}
    """
    if not object_name:
        raise ValueError("文件对象名不能为空")

    await db.initialize()
    tag_doc = await db.find_one(settings.collection_oss_file_tags, {"object_name": object_name})
    return tag_doc.get("tags", []) if tag_doc else []

async def delete_file_tags(object_name: str) -> bool:
    """
    删除文件的所有标签
    
    Example:
        GET /?module_name=services.storage.oss_client&method_name=delete_file_tags&parameters={"object_name": "images/test.jpg"}
    """
    if not object_name:
        raise ValueError("文件对象名不能为空")

    await db.initialize()
    deleted_count = await db.delete_one(settings.collection_oss_file_tags, {"object_name": object_name})
    return deleted_count > 0

async def get_all_tags() -> List[Dict[str, Any]]:
    """
    聚合所有标签及其使用计数
    
    Returns:
        List[Dict[str, Any]]: 标签统计列表，包含 name 和 count

    Example:
        GET /?module_name=services.storage.oss_client&method_name=get_all_tags&parameters={}
    """
    await db.initialize()
    tag_docs = await db.find_many(settings.collection_oss_file_tags, {})

    tag_count = {}
    for doc in tag_docs:
        for tag in doc.get("tags", []):
            tag_count[tag] = tag_count.get(tag, 0) + 1

    sorted_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)
    return [{"name": tag, "count": count} for tag, count in sorted_tags]

async def update_file_info(object_name: str, title: Optional[str] = None, description: Optional[str] = None) -> Dict[str, str]:
    """
    更新文件信息（标题/描述），自动维护时间戳
    
    Args:
        object_name: 文件对象名
        title: 标题 (可选)
        description: 描述 (可选)
        
    Returns:
        Dict[str, str]: 更新后的文件信息
        
    Raises:
        ValueError: 文件对象名为空

    Example:
        GET /?module_name=services.storage.oss_client&method_name=update_file_info&parameters={"object_name": "images/test.jpg", "title": "New Title"}
    """
    if not object_name:
        raise ValueError("文件对象名不能为空")

    update_data = {
        "object_name": object_name,
        "updatedTime": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    }

    if title is not None:
        update_data["title"] = title.strip() if title else ""
    if description is not None:
        update_data["description"] = description.strip() if description else ""

    await db.initialize()
    collection = db.db[settings.collection_oss_file_info]

    await collection.update_one(
        {"object_name": object_name},
        {
            "$set": update_data,
            "$setOnInsert": {
                "createdTime": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            }
        },
        upsert=True
    )
    
    return {
        "object_name": object_name,
        "title": title or "",
        "description": description or ""
    }

async def get_file_info(object_name: str) -> Dict[str, str]:
    """
    获取文件信息（标题/描述），不存在则返回空结构
    
    Example:
        GET /?module_name=services.storage.oss_client&method_name=get_file_info&parameters={"object_name": "images/test.jpg"}
    """
    if not object_name:
        raise ValueError("文件对象名不能为空")

    await db.initialize()
    info_doc = await db.find_one(settings.collection_oss_file_info, {"object_name": object_name})

    if info_doc:
        return {
            "object_name": object_name,
            "title": info_doc.get("title", ""),
            "description": info_doc.get("description", "")
        }
    else:
        return {
            "object_name": object_name,
            "title": "",
            "description": ""
        }

async def list_files(directory: Optional[str] = None, tags: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    列出目录下文件（支持标签过滤），返回基础元数据与标签/信息
    
    Example:
        GET /?module_name=services.storage.oss_client&method_name=list_files&parameters={"directory": "images/"}
    """
    config = OSSConfig()
    bucket = get_bucket(config)
    
    prefix = f"{directory}/" if directory else ""
    files = []

    for obj in oss2.ObjectIterator(bucket, prefix=prefix):
        last_modified_str = None
        if obj.last_modified:
            try:
                last_modified_dt = datetime.fromtimestamp(obj.last_modified, tz=timezone.utc)
                last_modified_str = last_modified_dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError, OSError):
                last_modified_str = str(obj.last_modified)

        file_tags = await get_file_tags(obj.key)
        file_info = await get_file_info(obj.key)

        file_data = {
            "name": obj.key,
            "size": obj.size,
            "size_human": f"{obj.size/1024/1024:.2f}MB",
            "last_modified": obj.last_modified,
            "last_modified_str": last_modified_str,
            "url": build_oss_url(bucket.bucket_name, bucket.endpoint, obj.key),
            "tags": file_tags,
            "title": file_info.get("title", ""),
            "description": file_info.get("description", "")
        }

        if tags:
            filter_tags = [t.strip() for t in tags.split(",") if t.strip()]
            if not any(tag in file_tags for tag in filter_tags):
                continue

        files.append(file_data)

    return files
