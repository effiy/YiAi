import os
import base64
import re
import logging
import shutil
from fastapi import APIRouter
from core.error_codes import ErrorCode
from core.exceptions import BusinessException
from core.schemas import FileUploadRequest, ImageUploadToOssRequest, FolderDeleteRequest, FileDeleteRequest, FileReadRequest, FileWriteRequest, FileRenameRequest, FolderRenameRequest
from core.response import success

logger = logging.getLogger(__name__)
router = APIRouter()

from core.settings import settings
from services.storage.oss_client import upload_bytes_to_oss

def _normalize_no_spaces(value: str) -> str:
    return re.sub(r"\s+", "_", (value or "").strip())

def _validate_path(path: str, param_name: str = "路径") -> str:
    """验证路径安全性，返回规范化的相对路径"""
    if not path or ".." in path or path.startswith("/"):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message=f"非法{param_name}")
    return path.strip().replace("\\", "/")

def _resolve_static_path(target_file: str) -> str:
    """将相对路径解析为安全的绝对路径"""
    rel = (target_file or "").strip().replace("\\", "/")
    if rel.startswith("static/"):
        rel = rel[7:]
    if not rel or rel.startswith("/") or ".." in rel:
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="非法路径")

    base_dir = os.path.realpath(os.path.abspath(settings.static_base_dir))
    abs_path = os.path.realpath(os.path.abspath(os.path.join(base_dir, os.path.normpath(rel))))

    if os.path.commonpath([base_dir, abs_path]) != base_dir:
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="非法路径")

    return abs_path

def _safe_rename(old_path: str, new_path: str, is_dir: bool = False) -> tuple[str, str]:
    """安全地重命名文件或目录，返回 (旧绝对路径, 新绝对路径)"""
    base_dir = os.path.abspath(settings.static_base_dir)

    # 构造绝对路径
    abs_old = os.path.join(base_dir, old_path)
    abs_new = os.path.join(base_dir, new_path)

    # 验证路径在 base_dir 内
    if not os.path.abspath(abs_old).startswith(base_dir):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="非法旧路径")
    if not os.path.abspath(abs_new).startswith(base_dir):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="非法新路径")

    # 检查源路径存在
    if not os.path.exists(abs_old):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message=f"原{'目录' if is_dir else '文件'}不存在: {old_path}")

    # 检查类型匹配
    if is_dir and not os.path.isdir(abs_old):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message=f"路径不是一个目录: {old_path}")
    if not is_dir and not os.path.isfile(abs_old):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message=f"路径不是一个文件: {old_path}")

    return abs_old, abs_new

@router.post("/upload-image-to-oss")
@router.post("/upload/upload-image-to-oss")
async def upload_image_to_oss(request: ImageUploadToOssRequest):
    raw = (request.data_url or "").strip()
    if not raw:
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="图片数据为空")

    base64_part = raw
    if raw.startswith("data:"):
        comma = raw.find(",")
        if comma < 0:
            raise BusinessException(ErrorCode.INVALID_PARAMS, message="图片数据格式错误")
        base64_part = raw[comma + 1 :].strip()

    try:
        content = base64.b64decode(base64_part, validate=True)
    except Exception:
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="Base64 解码失败")

    filename = _normalize_no_spaces(request.filename)
    directory = _normalize_no_spaces(request.directory or "aicr")
    result = await upload_bytes_to_oss(content, filename, directory=directory)
    return success(data=result)

@router.post("/read-file")
async def read_file(request: FileReadRequest):
    """
    读取文件接口
    """
    target_file = _normalize_no_spaces(request.target_file)
    found_path = _resolve_static_path(target_file)

    if not os.path.exists(found_path):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message=f"文件不存在: {target_file}")

    if not os.path.isfile(found_path):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message=f"路径不是一个文件: {target_file}")

    try:
        # 尝试以文本方式读取
        try:
            with open(found_path, "r", encoding="utf-8") as f:
                content = f.read()
                return success(data={"content": content, "type": "text"})
        except UnicodeDecodeError:
            # 如果不是文本文件，读取为 Base64
            with open(found_path, "rb") as f:
                content_bytes = f.read()
                content_base64 = base64.b64encode(content_bytes).decode('utf-8')
                return success(data={"content": content_base64, "type": "base64"})
                
    except Exception as e:
        logger.error(f"读取文件失败: {str(e)}", exc_info=True)
        raise BusinessException(ErrorCode.INTERNAL_ERROR, message=f"读取文件失败: {str(e)}")

@router.post("/write-file")
async def write_file(request: FileWriteRequest):
    """
    写入文件接口
    """
    target_file = _normalize_no_spaces(request.target_file)
    content = request.content
    is_base64 = request.is_base64

    target_path = _resolve_static_path(target_file)
    
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        if is_base64:
             content_bytes = base64.b64decode(content)
             with open(target_path, "wb") as f:
                 f.write(content_bytes)
        else:
             with open(target_path, "w", encoding="utf-8") as f:
                 f.write(content)
                 
        return success(data={"message": "保存成功", "path": target_path})
    except Exception as e:
        logger.error(f"写入文件失败: {str(e)}", exc_info=True)
        raise BusinessException(ErrorCode.INTERNAL_ERROR, message=f"写入文件失败: {str(e)}")

@router.post("/delete-file")
async def delete_file(request: FileDeleteRequest):
    """
    删除文件接口
    """
    target_file = _normalize_no_spaces(request.target_file)
    _validate_path(target_file)

    abs_path = _resolve_static_path(target_file)

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
    target_dir = _normalize_no_spaces(request.target_dir)
    _validate_path(target_dir)

    abs_path = _resolve_static_path(target_dir)

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

@router.post("/rename-file")
async def rename_file(request: FileRenameRequest):
    """
    重命名文件接口
    """
    old_path_str = _validate_path(request.old_path, "旧路径")
    new_path_str = _validate_path(_normalize_no_spaces(request.new_path), "新路径")

    abs_old, abs_new = _safe_rename(old_path_str, new_path_str, is_dir=False)

    try:
        os.makedirs(os.path.dirname(abs_new), exist_ok=True)
        os.rename(abs_old, abs_new)
        logger.info(f"成功重命名文件: {abs_old} -> {abs_new}")
    except Exception as e:
        logger.error(f"重命名文件失败: {str(e)}", exc_info=True)
        raise BusinessException(ErrorCode.INTERNAL_ERROR, message=f"重命名文件失败: {str(e)}")

    return success(data={"message": "重命名成功", "old_path": old_path_str, "new_path": new_path_str})

@router.post("/rename-folder")
async def rename_folder(request: FolderRenameRequest):
    """
    重命名文件夹接口
    """
    old_dir_str = _validate_path(request.old_dir, "旧路径")
    new_dir_str = _validate_path(_normalize_no_spaces(request.new_dir), "新路径")

    abs_old, abs_new = _safe_rename(old_dir_str, new_dir_str, is_dir=True)

    try:
        os.makedirs(os.path.dirname(abs_new), exist_ok=True)
        os.rename(abs_old, abs_new)
        logger.info(f"成功重命名文件夹: {abs_old} -> {abs_new}")
    except Exception as e:
        logger.error(f"重命名文件夹失败: {str(e)}", exc_info=True)
        raise BusinessException(ErrorCode.INTERNAL_ERROR, message=f"重命名文件夹失败: {str(e)}")

    return success(data={"message": "重命名成功", "old_path": old_dir_str, "new_path": new_dir_str})

@router.post("/upload")
async def upload_file(request: FileUploadRequest):
    """
    文件上传接口 (JSON 方式)
    """
    target_dir = _normalize_no_spaces(request.target_dir)
    # 确保目录存在 (相对于当前工作目录)
    save_dir = os.path.join(os.getcwd(), target_dir)
    os.makedirs(save_dir, exist_ok=True)
    
    filename = _normalize_no_spaces(request.filename)
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
