from fastapi.responses import JSONResponse
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body

import oss2, os, logging
from datetime import datetime, timezone
from typing import Optional, Any, List
from functools import lru_cache, wraps

from database import db
from Resp import RespOk

# 设置日志
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

def build_oss_url(bucket_name: str, endpoint: str, object_key: str) -> str:
    """构建OSS文件的访问URL"""
    # 移除 endpoint 中可能存在的协议头
    clean_endpoint = endpoint.replace('http://', '').replace('https://', '')
    return f"https://{bucket_name}.{clean_endpoint}/{object_key}"

router = APIRouter(
    prefix="/oss",
    tags=["阿里云OSS"],
    responses={404: {"description": "未找到"}},
)

# 文件上传配置
# 从环境变量读取最大文件大小，默认 50MB
MAX_FILE_SIZE = int(os.getenv("OSS_MAX_FILE_SIZE", "50")) * 1024 * 1024  # 默认 50MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.epub'}

class OSSConfig:
    def __init__(self):
        self.access_key_id = os.getenv("OSS_ACCESS_KEY_ID")
        self.access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET")
        self.endpoint = os.getenv("OSS_ENDPOINT")
        self.bucket_name = os.getenv("OSS_BUCKET_NAME")

        if not all([self.access_key_id, self.access_key_secret, self.endpoint, self.bucket_name]):
            raise ValueError("OSS配置不完整，请检查环境变量")

@lru_cache()
def get_oss_config() -> OSSConfig:
    return OSSConfig()

@lru_cache()
def get_bucket(config: OSSConfig = Depends(get_oss_config)):
    auth = oss2.Auth(config.access_key_id, config.access_key_secret)
    return oss2.Bucket(auth, config.endpoint, config.bucket_name)

def validate_file(file: UploadFile) -> None:
    """验证文件大小和类型"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型: {file_ext}，支持的类型: {', '.join(ALLOWED_EXTENSIONS)}"
        )

@router.delete("/")
@ensure_initialized()
async def delete(osspath: str):
    """删除OSS文件"""
    try:
        if not osspath:
            raise HTTPException(status_code=400, detail="文件路径不能为空")
        
        bucket = get_bucket()
        bucket.delete_object(osspath)
        return RespOk()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除OSS文件失败: {str(e)}")
        return handle_error(e, 500)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    directory: Optional[str] = None,
    bucket: oss2.Bucket = Depends(get_bucket),
    config: OSSConfig = Depends(get_oss_config)
) -> JSONResponse:
    """上传单个文件到OSS"""
    try:
        # 验证文件
        validate_file(file)

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"文件大小超过限制: {MAX_FILE_SIZE/1024/1024}MB"
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(file.filename)[1]
        object_name = f"{directory + '/' if directory else ''}{timestamp}{file_ext}"

        bucket.put_object(object_name, content)
        file_url = build_oss_url(config.bucket_name, config.endpoint, object_name)

        logger.info(f"文件上传成功: {object_name}")
        return create_response(
            code=200,
            message="上传成功",
            data={
                "url": file_url,
                "filename": file.filename,
                "object_name": object_name
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        return handle_error(e, 500)

@router.delete("/delete/{object_name:path}")
async def delete_file(
    object_name: str,
    bucket: oss2.Bucket = Depends(get_bucket)
) -> JSONResponse:
    """删除OSS中的单个文件"""
    try:
        if not object_name:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        exists = bucket.object_exists(object_name)
        if not exists:
            raise HTTPException(status_code=404, detail="文件不存在")

        bucket.delete_object(object_name)
        
        # 同时删除文件的标签信息
        try:
            await db.mongodb.initialize()
            await db.mongodb.delete_one("oss_file_tags", {"object_name": object_name})
        except Exception as tag_error:
            logger.warning(f"删除文件标签失败: {str(tag_error)}")
        
        # 同时删除文件的信息（标题、描述等）
        try:
            await db.mongodb.initialize()
            await db.mongodb.delete_one("oss_file_info", {"object_name": object_name})
        except Exception as info_error:
            logger.warning(f"删除文件信息失败: {str(info_error)}")
        
        logger.info(f"文件删除成功: {object_name}")

        return create_response(
            code=200,
            message="删除成功",
            data={"object_name": object_name}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        return handle_error(e, 500)

@router.post("/tags")
@ensure_initialized()
async def set_file_tags(
    object_name: str = Body(..., description="文件对象名"),
    tags: List[str] = Body(..., description="标签列表")
) -> JSONResponse:
    """为文件设置标签"""
    try:
        if not object_name:
            raise HTTPException(status_code=400, detail="文件对象名不能为空")
        
        # 验证标签格式（去重、去空）
        tags = [tag.strip() for tag in tags if tag.strip()]
        tags = list(set(tags))  # 去重
        
        # 使用 upsert 操作
        await db.mongodb.initialize()
        collection = db.mongodb.db["oss_file_tags"]
        
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
        
        logger.info(f"文件标签设置成功: {object_name}, 标签: {tags}")
        return create_response(
            code=200,
            message="标签设置成功",
            data={"object_name": object_name, "tags": tags}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置文件标签失败: {str(e)}")
        return handle_error(e, 500)

@router.get("/tags/{object_name:path}")
@ensure_initialized()
async def get_file_tags(object_name: str) -> JSONResponse:
    """获取文件的标签"""
    try:
        if not object_name:
            raise HTTPException(status_code=400, detail="文件对象名不能为空")
        
        await db.mongodb.initialize()
        tag_doc = await db.mongodb.find_one("oss_file_tags", {"object_name": object_name})
        
        tags = tag_doc.get("tags", []) if tag_doc else []
        
        return create_response(
            code=200,
            message="获取成功",
            data={"object_name": object_name, "tags": tags}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件标签失败: {str(e)}")
        return handle_error(e, 500)

@router.delete("/tags/{object_name:path}")
@ensure_initialized()
async def delete_file_tags(object_name: str) -> JSONResponse:
    """删除文件的所有标签"""
    try:
        if not object_name:
            raise HTTPException(status_code=400, detail="文件对象名不能为空")
        
        await db.mongodb.initialize()
        deleted_count = await db.mongodb.delete_one("oss_file_tags", {"object_name": object_name})
        
        logger.info(f"文件标签删除成功: {object_name}")
        return create_response(
            code=200,
            message="标签删除成功",
            data={"object_name": object_name, "deleted": deleted_count > 0}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件标签失败: {str(e)}")
        return handle_error(e, 500)

@router.get("/tags")
@ensure_initialized()
async def get_all_tags() -> JSONResponse:
    """获取所有标签列表"""
    try:
        await db.mongodb.initialize()
        tag_docs = await db.mongodb.find_many("oss_file_tags", {})
        
        # 收集所有标签并统计使用次数
        tag_count = {}
        for doc in tag_docs:
            for tag in doc.get("tags", []):
                tag_count[tag] = tag_count.get(tag, 0) + 1
        
        # 按使用次数排序
        sorted_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)
        
        tags_list = [{"name": tag, "count": count} for tag, count in sorted_tags]
        
        return create_response(
            code=200,
            message="获取成功",
            data=tags_list
        )
    except Exception as e:
        logger.error(f"获取所有标签失败: {str(e)}")
        return handle_error(e, 500)

@router.get("/files")
async def list_files(
    directory: Optional[str] = None,
    max_keys: int = 100,
    tags: Optional[str] = None,
    bucket: oss2.Bucket = Depends(get_bucket)
) -> JSONResponse:
    """列出OSS中的文件（支持标签筛选）"""
    try:
        if max_keys > 1000:
            raise HTTPException(status_code=400, detail="max_keys不能超过1000")
        
        if max_keys < 1:
            raise HTTPException(status_code=400, detail="max_keys必须大于0")

        prefix = f"{directory}/" if directory else ""
        files = []

        for obj in oss2.ObjectIterator(bucket, prefix=prefix, max_keys=max_keys):
            # 格式化最后修改时间
            last_modified_str = None
            if obj.last_modified:
                # 将时间戳转换为格式化的字符串
                try:
                    last_modified_dt = datetime.fromtimestamp(obj.last_modified, tz=timezone.utc)
                    last_modified_str = last_modified_dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError, OSError):
                    last_modified_str = str(obj.last_modified)
            
            # 获取文件的标签
            file_tags = []
            try:
                await db.initialize()
                tag_doc = await db.mongodb.find_one("oss_file_tags", {"object_name": obj.key})
                if tag_doc:
                    file_tags = tag_doc.get("tags", [])
            except Exception as tag_error:
                logger.warning(f"获取文件标签失败: {str(tag_error)}")
            
            file_data = {
                "name": obj.key,
                "size": obj.size,
                "size_human": f"{obj.size/1024/1024:.2f}MB",
                "last_modified": obj.last_modified,
                "last_modified_str": last_modified_str,
                "url": build_oss_url(bucket.bucket_name, bucket.endpoint, obj.key),
                "tags": file_tags
            }
            
            # 如果指定了标签筛选，则只返回包含该标签的文件
            if tags:
                filter_tags = [t.strip() for t in tags.split(",") if t.strip()]
                if not any(tag in file_tags for tag in filter_tags):
                    continue
            
            files.append(file_data)

        logger.info(f"成功获取文件列表，共{len(files)}个文件")
        return create_response(code=200, message="获取成功", data=files)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        return handle_error(e, 500)

@router.post("/file/info")
@ensure_initialized()
async def update_file_info(
    object_name: str = Body(..., description="文件对象名"),
    title: Optional[str] = Body(None, description="文件标题"),
    description: Optional[str] = Body(None, description="文件描述")
) -> JSONResponse:
    """更新文件信息（标题、描述等）"""
    try:
        if not object_name:
            raise HTTPException(status_code=400, detail="文件对象名不能为空")
        
        # 准备更新数据
        update_data = {
            "object_name": object_name,
            "updatedTime": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if title is not None:
            update_data["title"] = title.strip() if title else ""
        if description is not None:
            update_data["description"] = description.strip() if description else ""
        
        # 使用 upsert 操作
        await db.mongodb.initialize()
        collection = db.mongodb.db["oss_file_info"]
        
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
        
        logger.info(f"文件信息更新成功: {object_name}, title: {title}, description: {description}")
        return create_response(
            code=200,
            message="更新成功",
            data={
                "object_name": object_name,
                "title": title or "",
                "description": description or ""
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新文件信息失败: {str(e)}")
        return handle_error(e, 500)

@router.get("/file/info/{object_name:path}")
@ensure_initialized()
async def get_file_info(object_name: str) -> JSONResponse:
    """获取文件信息（标题、描述等）"""
    try:
        if not object_name:
            raise HTTPException(status_code=400, detail="文件对象名不能为空")
        
        await db.mongodb.initialize()
        info_doc = await db.mongodb.find_one("oss_file_info", {"object_name": object_name})
        
        if info_doc:
            return create_response(
                code=200,
                message="获取成功",
                data={
                    "object_name": object_name,
                    "title": info_doc.get("title", ""),
                    "description": info_doc.get("description", "")
                }
            )
        else:
            return create_response(
                code=200,
                message="获取成功",
                data={
                    "object_name": object_name,
                    "title": "",
                    "description": ""
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件信息失败: {str(e)}")
        return handle_error(e, 500)
