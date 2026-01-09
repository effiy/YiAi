import os
import base64
import logging
import shutil
from fastapi import APIRouter
from core.error_codes import ErrorCode
from core.exceptions import BusinessException
from core.schemas import FileUploadRequest, FolderDeleteRequest, FileDeleteRequest
from core.response import success

logger = logging.getLogger(__name__)
router = APIRouter()

from core.settings import settings

@router.post("/delete-file")
async def delete_file(request: FileDeleteRequest):
    """
    删除文件接口
    """
    target_file = request.target_file
    # 安全检查
    if not target_file or '..' in target_file or target_file.startswith('/'):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="非法路径")

    # 构造绝对路径
    base_dir = os.path.abspath(settings.static_base_dir)
    abs_path = os.path.join(base_dir, target_file)
    
    # 路径遍历检查
    if not os.path.abspath(abs_path).startswith(base_dir):
         raise BusinessException(ErrorCode.INVALID_PARAMS, message="非法路径")

    if not os.path.exists(abs_path):
        return success(data={"message": "文件不存在", "path": target_file})

    if not os.path.isfile(abs_path):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message=f"路径不是一个文件: {target_file}")

    try:
        os.remove(abs_path)
        logger.info(f"成功删除文件: {abs_path}")
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}", exc_info=True)
        raise BusinessException(ErrorCode.DATA_DESTROY_FAIL, message=f"删除文件失败: {str(e)}")
        
    return success(data={"message": "删除成功", "path": target_file})

@router.post("/delete-folder")
async def delete_folder(request: FolderDeleteRequest):
    """
    删除文件夹接口
    """
    target_dir = request.target_dir
    # 安全检查
    if not target_dir or '..' in target_dir or target_dir.startswith('/'):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="非法路径")

    # 构造绝对路径：使用 settings.static_base_dir 作为基准
    # 这样前端传递 "foo/bar" 会被映射到 "static/foo/bar" (假设 static_base_dir="./static")
    base_dir = os.path.abspath(settings.static_base_dir)
    abs_path = os.path.join(base_dir, target_dir)
    
    # 再次检查路径是否在 base_dir 下，防止路径遍历攻击
    if not os.path.abspath(abs_path).startswith(base_dir):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="非法路径")

    if not os.path.exists(abs_path):
        return success(data={"message": "目录不存在", "path": target_dir})

    if not os.path.isdir(abs_path):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message=f"路径不是一个目录: {target_dir}")

    try:
        shutil.rmtree(abs_path)
        logger.info(f"成功删除目录: {abs_path}")
    except Exception as e:
        logger.error(f"删除目录失败: {str(e)}", exc_info=True)
        raise BusinessException(ErrorCode.DATA_DESTROY_FAIL, message=f"删除目录失败: {str(e)}")
        
    return success(data={"message": "删除成功", "path": target_dir})

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
