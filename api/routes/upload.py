import os
import base64
import logging
import shutil
from fastapi import APIRouter
from core.error_codes import ErrorCode
from core.exceptions import BusinessException
from core.schemas import FileUploadRequest, FolderDeleteRequest, FileDeleteRequest, FileReadRequest, FileWriteRequest
from core.response import success

logger = logging.getLogger(__name__)
router = APIRouter()

from core.settings import settings

@router.post("/read-file")
async def read_file(request: FileReadRequest):
    """
    读取文件接口
    """
    target_file = request.target_file
    # 安全检查
    if not target_file or '..' in target_file or target_file.startswith('/'):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="非法路径")

    # 构造绝对路径
    base_dir = os.path.abspath(settings.static_base_dir)
    abs_path = os.path.join(base_dir, target_file)
    
    found_path = None
    
    # 1. 尝试在 static_base_dir 中查找
    if os.path.exists(abs_path) and os.path.isfile(abs_path):
        # 路径遍历检查
        if os.path.abspath(abs_path).startswith(base_dir):
            found_path = abs_path

    # 2. 如果未找到，尝试在项目根目录下的其他子目录中查找 (Monorepo 支持)
    if not found_path:
        # 假设当前工作目录是 YiAi，项目根目录是上一级
        current_dir = os.getcwd()
        project_root = os.path.abspath(os.path.join(current_dir, ".."))
        
        # 简单的安全检查：确保我们在预期的目录结构中
        # 遍历项目根目录下的子目录 (e.g., YiPet, YiWeb)
        try:
            if os.path.exists(project_root) and os.path.isdir(project_root):
                for item in os.listdir(project_root):
                    subdir = os.path.join(project_root, item)
                    # 跳过隐藏目录和当前目录 (YiAi)
                    if os.path.isdir(subdir) and not item.startswith('.') and subdir != current_dir:
                        candidate = os.path.join(subdir, target_file)
                        if os.path.exists(candidate) and os.path.isfile(candidate):
                            # 安全检查：必须在项目根目录下
                            if os.path.abspath(candidate).startswith(project_root):
                                found_path = candidate
                                logger.info(f"在兄弟目录中找到文件: {found_path}")
                                break
        except Exception as e:
            logger.warn(f"搜索兄弟目录失败: {e}")

    if not found_path:
        raise BusinessException(ErrorCode.INVALID_PARAMS, message=f"文件不存在: {target_file}")

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
    target_file = request.target_file
    content = request.content
    is_base64 = request.is_base64

    # 安全检查
    if not target_file or '..' in target_file or target_file.startswith('/'):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="非法路径")

    # 构造绝对路径
    base_dir = os.path.abspath(settings.static_base_dir)
    abs_path = os.path.join(base_dir, target_file)
    
    found_path = None
    
    # 1. 尝试在 static_base_dir 中查找
    if os.path.exists(abs_path) and os.path.isfile(abs_path):
        # 路径遍历检查
        if os.path.abspath(abs_path).startswith(base_dir):
            found_path = abs_path

    # 2. 如果未找到，尝试在项目根目录下的其他子目录中查找 (Monorepo 支持)
    if not found_path:
        current_dir = os.getcwd()
        project_root = os.path.abspath(os.path.join(current_dir, ".."))
        
        try:
            if os.path.exists(project_root) and os.path.isdir(project_root):
                for item in os.listdir(project_root):
                    subdir = os.path.join(project_root, item)
                    # 跳过隐藏目录和当前目录 (YiAi)
                    if os.path.isdir(subdir) and not item.startswith('.') and subdir != current_dir:
                        candidate = os.path.join(subdir, target_file)
                        if os.path.exists(candidate) and os.path.isfile(candidate):
                            # 安全检查：必须在项目根目录下
                            if os.path.abspath(candidate).startswith(project_root):
                                found_path = candidate
                                logger.info(f"在兄弟目录中找到文件: {found_path}")
                                break
        except Exception as e:
            logger.warn(f"搜索兄弟目录失败: {e}")

    # 确定最终写入路径：如果找到现有文件则覆盖，否则默认在 static_base_dir 下创建
    target_path = found_path if found_path else abs_path
    
    try:
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
