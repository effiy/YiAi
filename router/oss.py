from fastapi.responses import JSONResponse # type: ignore
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends # type: ignore

import oss2, os, logging # type: ignore
from datetime import datetime
from typing import Optional, Any
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

router = APIRouter(
    prefix="/oss",
    tags=["阿里云OSS"],
    responses={404: {"description": "未找到"}},
)

# 文件上传配置
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx'}

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
    file_ext = os.path.splitext(file.filename)[1].lower() # type: ignore
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")

@router.delete("/")
@ensure_initialized()
async def delete(osspath: str):
    """删除OSS文件"""
    try:
        bucket = get_bucket()
        bucket.delete_object(osspath)
        return RespOk()
    except Exception as e:
        return handle_error(e)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    directory: Optional[str] = None,
    bucket: oss2.Bucket = Depends(get_bucket),
    config: OSSConfig = Depends(get_oss_config)
) -> JSONResponse:
    """上传单个文件到OSS"""
    try:
        validate_file(file)
        
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            return create_response(code=400, message=f"文件大小超过限制: {MAX_FILE_SIZE/1024/1024}MB")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(file.filename)[1] # type: ignore
        object_name = f"{directory + '/' if directory else ''}{timestamp}{file_ext}"
        
        bucket.put_object(object_name, content)
        file_url = f"https://{config.bucket_name}.{config.endpoint}/{object_name}"
        
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
    except Exception as e:
        return handle_error(e)

@router.get("/files")
async def list_files(
    directory: Optional[str] = None,
    max_keys: int = 100,
    bucket: oss2.Bucket = Depends(get_bucket)
) -> JSONResponse:
    """列出OSS中的文件"""
    try:
        if max_keys > 1000:
            return create_response(code=400, message="max_keys不能超过1000")
        
        prefix = f"{directory}/" if directory else ""
        files = []
        
        for obj in oss2.ObjectIterator(bucket, prefix=prefix, max_keys=max_keys):
            files.append({
                "name": obj.key,
                "size": obj.size,
                "size_human": f"{obj.size/1024/1024:.2f}MB",
                "last_modified": obj.last_modified,
                "url": f"https://{bucket.bucket_name}.{bucket.endpoint}/{obj.key}"
            })
        
        logger.info(f"成功获取文件列表，共{len(files)}个文件")
        return create_response(code=200, message="获取成功", data=files)
    except Exception as e:
        return handle_error(e)

@router.delete("/delete/{object_name:path}")
async def delete_file(
    object_name: str,
    bucket: oss2.Bucket = Depends(get_bucket)
) -> JSONResponse:
    """删除OSS中的单个文件"""
    try:
        exists = bucket.object_exists(object_name)
        if not exists:
            return create_response(code=404, message="文件不存在")
        
        bucket.delete_object(object_name)
        logger.info(f"文件删除成功: {object_name}")
        
        return create_response(
            code=200,
            message="删除成功",
            data={"object_name": object_name}
        )
    except Exception as e:
        return handle_error(e) 