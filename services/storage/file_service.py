"""OSS 存储服务
- 提供文件上传/删除、标签管理、文件信息维护与列表查询
- 包含核心业务逻辑与动态执行适配接口
"""
import os
import oss2
import logging
import base64
from typing import Optional, List, Dict, Any
from fastapi import UploadFile, HTTPException
from datetime import datetime, timezone
from core.settings import settings
from core.database import db

logger = logging.getLogger(__name__)

# --- Core Implementation (formerly oss_client.py) ---

class OSSConfig:
    """从配置加载 OSS 连接参数"""
    def __init__(self):
        self.access_key_id = settings.oss_access_key
        self.access_key_secret = settings.oss_secret_key
        self.endpoint = settings.oss_endpoint
        self.bucket_name = settings.oss_bucket

        if not all([self.access_key_id, self.access_key_secret, self.endpoint, self.bucket_name]):
            logger.warning("OSS config incomplete.")

def get_bucket(config: OSSConfig) -> oss2.Bucket:
    auth = oss2.Auth(config.access_key_id, config.access_key_secret)
    return oss2.Bucket(auth, config.endpoint, config.bucket_name)

def build_oss_url(bucket_name: str, endpoint: str, object_key: str) -> str:
    clean_endpoint = endpoint.replace('http://', '').replace('https://', '')
    return f"https://{bucket_name}.{clean_endpoint}/{object_key}"

async def upload_file_to_oss(file: UploadFile, directory: Optional[str] = None) -> dict:
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

async def delete_oss_file(object_name: str):
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
    if not object_name:
        raise ValueError("文件对象名不能为空")

    await db.initialize()
    tag_doc = await db.find_one(settings.collection_oss_file_tags, {"object_name": object_name})
    return tag_doc.get("tags", []) if tag_doc else []

async def delete_file_tags(object_name: str) -> bool:
    if not object_name:
        raise ValueError("文件对象名不能为空")

    await db.initialize()
    deleted_count = await db.delete_one(settings.collection_oss_file_tags, {"object_name": object_name})
    return deleted_count > 0

async def get_all_tags() -> List[Dict[str, Any]]:
    await db.initialize()
    tag_docs = await db.find_many(settings.collection_oss_file_tags, {})
    tag_count = {}
    for doc in tag_docs:
        for tag in doc.get("tags", []):
            tag_count[tag] = tag_count.get(tag, 0) + 1

    sorted_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)
    return [{"name": tag, "count": count} for tag, count in sorted_tags]

async def update_file_info(object_name: str, title: Optional[str] = None, description: Optional[str] = None) -> Dict[str, str]:
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

async def list_files_impl(directory: Optional[str] = None, tags: Optional[str] = None) -> List[Dict[str, Any]]:
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

# --- Adapter Interface (formerly file_service.py) ---

async def delete_file(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    删除 OSS 文件
    Args:
        params: {"object_name": "..."} or {"osspath": "..."}
    """
    object_name = params.get('object_name') or params.get('osspath')
    if not object_name:
        raise ValueError("object_name or osspath is required")
        
    await delete_oss_file(object_name)
    return {"success": True, "object_name": object_name}

async def list_files(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    列出文件
    Args:
        params: {"directory": "...", "tags": "..."}
    """
    directory = params.get('directory')
    tags = params.get('tags')
    return await list_files_impl(directory, tags)

async def set_tags(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    设置标签
    Args:
        params: {"object_name": "...", "tags": [...]}
    """
    object_name = params.get('object_name')
    tags = params.get('tags', [])
    
    if not object_name:
        raise ValueError("object_name is required")
        
    return await set_file_tags(object_name, tags)

async def get_tags(params: Dict[str, Any]) -> List[str]:
    """
    获取标签
    Args:
        params: {"object_name": "..."}
    """
    object_name = params.get('object_name')
    if not object_name:
        raise ValueError("object_name is required")
        
    return await get_file_tags(object_name)

async def update_info(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    更新文件信息
    Args:
        params: {"object_name": "...", "title": "...", "description": "..."}
    """
    object_name = params.get('object_name')
    title = params.get('title')
    description = params.get('description')
    
    if not object_name:
        raise ValueError("object_name is required")
        
    return await update_file_info(object_name, title, description)

async def get_info(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取文件信息
    Args:
        params: {"object_name": "..."}
    """
    object_name = params.get('object_name')
    if not object_name:
        raise ValueError("object_name is required")
        
    return await get_file_info(object_name)
