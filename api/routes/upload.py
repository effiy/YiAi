import os
import base64
import logging
from fastapi import APIRouter
from core.schemas import FileUploadRequest
from core.response import success

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload")
async def upload_file(request: FileUploadRequest):
    """
    文件上传接口 (JSON 方式)
    """
    target_dir = request.target_dir
    # 确保目录存在 (相对于当前工作目录)
    save_dir = os.path.join(os.getcwd(), target_dir)
    os.makedirs(save_dir, exist_ok=True)
    
    filename = request.filename
    file_path = os.path.join(save_dir, filename)
    
    try:
        if request.is_base64:
            # Base64 解码并写入二进制文件
            content_bytes = base64.b64decode(request.content)
            with open(file_path, "wb") as f:
                f.write(content_bytes)
        else:
            # 直接写入文本文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(request.content)
    except Exception as e:
        logger.error(f"文件保存失败: {str(e)}", exc_info=True)
        raise ValueError(f"文件保存失败: {str(e)}")
        
    # 返回相对路径
    rel_path = f"/{target_dir}/{filename}"
    # 统一路径分隔符
    rel_path = rel_path.replace(os.sep, '/')
    # 确保不以 // 开头 (如果 target_dir 为空或 / 开头)
    if rel_path.startswith('//'):
        rel_path = rel_path[1:]
        
    return success(data={"url": rel_path})
