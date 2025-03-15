from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import oss2 # type: ignore
from typing import Optional
import os
from datetime import datetime

router = APIRouter(
    prefix="/oss",
    tags=["阿里云OSS"],
    responses={404: {"description": "未找到"}},
)

# OSS配置
access_key_id = os.getenv("OSS_ACCESS_KEY_ID")
access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET")
endpoint = os.getenv("OSS_ENDPOINT")
bucket_name = os.getenv("OSS_BUCKET_NAME")

# 初始化OSS客户端
auth = oss2.Auth(access_key_id, access_key_secret)
bucket = oss2.Bucket(auth, endpoint, bucket_name)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), directory: Optional[str] = None):
    """
    上传文件到OSS
    :param file: 要上传的文件
    :param directory: 可选的目录路径
    :return: 上传成功后的文件URL
    """
    try:
        # 生成文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(file.filename)[1]
        object_name = f"{directory + '/' if directory else ''}{timestamp}{file_ext}"
        
        # 读取文件内容并上传
        content = await file.read()
        bucket.put_object(object_name, content)
        
        # 生成文件URL
        file_url = f"https://{bucket_name}.{endpoint}/{object_name}"
        
        return JSONResponse(
            content={
                "code": 200,
                "message": "上传成功",
                "data": {
                    "url": file_url,
                    "filename": file.filename,
                    "object_name": object_name
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files")
async def list_files(directory: Optional[str] = None, max_keys: int = 100):
    """
    列出OSS中的文件
    :param directory: 可选的目录路径
    :param max_keys: 最大返回数量
    :return: 文件列表
    """
    try:
        prefix = f"{directory}/" if directory else ""
        files = []
        
        for obj in oss2.ObjectIterator(bucket, prefix=prefix, max_keys=max_keys):
            files.append({
                "name": obj.key,
                "size": obj.size,
                "last_modified": obj.last_modified,
                "url": f"https://{bucket_name}.{endpoint}/{obj.key}"
            })
            
        return JSONResponse(
            content={
                "code": 200,
                "message": "获取成功",
                "data": files
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{object_name:path}")
async def delete_file(object_name: str):
    """
    删除OSS中的文件
    :param object_name: 文件的对象名称
    :return: 删除结果
    """
    try:
        exists = bucket.object_exists(object_name)
        if not exists:
            raise HTTPException(status_code=404, detail="文件不存在")
            
        bucket.delete_object(object_name)
        
        return JSONResponse(
            content={
                "code": 200,
                "message": "删除成功",
                "data": {"object_name": object_name}
            }
        )
    except oss2.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="文件不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 