import os
import base64
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

def _resolve_static_path(target_file: str) -> str:
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

    result = await upload_bytes_to_oss(content, request.filename, directory=(request.directory or "aicr"))
    return success(data=result)

@router.post("/read-file")
async def read_file(request: FileReadRequest):
    """
    读取文件接口
    """
    target_file = request.target_file
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
    target_file = request.target_file
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

@router.post("/rename-file")
async def rename_file(request: FileRenameRequest):
    """
    重命名文件接口
    """
    old_path_str = request.old_path
    new_path_str = request.new_path

    # 安全检查
    if not old_path_str or '..' in old_path_str or old_path_str.startswith('/'):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="非法旧路径")
    if not new_path_str or '..' in new_path_str or new_path_str.startswith('/'):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="非法新路径")

    # 构造绝对路径
    base_dir = os.path.abspath(settings.static_base_dir)
    abs_old_path = os.path.join(base_dir, old_path_str)
    
    found_old_path = None
    
    # 1. 尝试在 static_base_dir 中查找
    if os.path.exists(abs_old_path) and os.path.isfile(abs_old_path):
        if os.path.abspath(abs_old_path).startswith(base_dir):
            found_old_path = abs_old_path

    # 2. 如果未找到，尝试在项目根目录下的其他子目录中查找
    if not found_old_path:
        current_dir = os.getcwd()
        project_root = os.path.abspath(os.path.join(current_dir, ".."))
        try:
            if os.path.exists(project_root) and os.path.isdir(project_root):
                for item in os.listdir(project_root):
                    subdir = os.path.join(project_root, item)
                    if os.path.isdir(subdir) and not item.startswith('.') and subdir != current_dir:
                        candidate = os.path.join(subdir, old_path_str)
                        if os.path.exists(candidate) and os.path.isfile(candidate):
                            if os.path.abspath(candidate).startswith(project_root):
                                found_old_path = candidate
                                logger.info(f"在兄弟目录中找到文件: {found_old_path}")
                                break
        except Exception as e:
            logger.warn(f"搜索兄弟目录失败: {e}")

    if not found_old_path:
        raise BusinessException(ErrorCode.INVALID_PARAMS, message=f"原文件不存在: {old_path_str}")

    # 计算新文件的绝对路径
    # 注意：新文件应该在原文件所在的目录或相对位置
    # 这里我们假设 new_path 也是相对于 base_dir 或者 project root 的路径
    # 为了简单和安全，我们假设 rename 操作是在同一个 base 根基下进行的
    
    # 确定 found_old_path 是相对于哪个 base 的
    # 如果 found_old_path startswith base_dir -> base is base_dir
    # 否则 -> base is project_root (unsafe? no, we checked it starts with project_root)
    
    target_base = base_dir
    if not found_old_path.startswith(base_dir):
        # 说明是在兄弟目录找到的
        # 我们需要反推 new_path 的绝对路径
        # 简单策略：new_path 必须也是相对路径，我们将其解析为相对于 found_old_path 的父目录？
        # 不，前端传来的 usually 是 "src/views/..." 这种
        # 如果 old_path="YiWeb/src/index.js", found at ".../YiWeb/src/index.js"
        # new_path="YiWeb/src/index2.js"
        
        # 让我们看看 read_file 是怎么找的
        # 它遍历了 subdir (e.g. YiWeb)，然后 join(subdir, target_file)
        # 所以 target_file 包含了 "src/..." 部分吗？
        # 还是 target_file 就是 "YiWeb/src/..." ?
        # 前端 store.js 中 normalizeFilePath 通常返回 relative path like "src/views/..."
        # 但是 backend read_file logic: candidate = os.path.join(subdir, target_file)
        # 这意味着如果 target_file="src/index.js", subdir="YiWeb", then check "YiWeb/src/index.js"
        # 
        # 如果 rename 传入的 old_path="src/index.js", new_path="src/index2.js"
        # 我们找到了 "YiWeb/src/index.js".
        # 那么 new_abs_path 应该是 "YiWeb/src/index2.js"
        
        # 我们需要知道 found_old_path 是通过哪个 root 找到的
        # found_old_path = .../YiWeb/src/index.js
        # old_path_str = src/index.js
        # root = found_old_path - old_path_str ?
        
        if found_old_path.endswith(old_path_str):
             root_len = len(found_old_path) - len(old_path_str)
             root_path = found_old_path[:root_len]
             abs_new_path = os.path.join(root_path, new_path_str)
        else:
             # Fallback: just join with dir name of old path?
             # 如果 old_path_str 不匹配结尾（路径分隔符差异？），这比较危险
             # 假设 path sep 是一致的
             dir_name = os.path.dirname(found_old_path)
             # 如果 new_path 和 old_path 在同一目录，new_path 可能只是文件名？
             # 不，前端传的是完整相对路径
             # 假设 new_path_str 也是相对于同一个 root
             # 重新计算 root
             # 简单起见，如果是在 base_dir 下，root=base_dir
             # 如果是在 sibling 下，我们尝试找到匹配的 sibling
             
             # 重新复用查找逻辑来定位 root
             # 但为了简单，我们可以利用 os.path.relpath?
             pass
             # 让我们采用简单的替换策略：
             # abs_new_path = found_old_path.replace(old_path_str, new_path_str) ?
             # 只有当 new_path_str 只是 old_path_str 的一部分变化时才行
             # 但如果是 mv src/a.js src/b/a.js 呢？
             pass
    
    # 重新确定 abs_new_path
    if found_old_path.startswith(base_dir):
         abs_new_path = os.path.join(base_dir, new_path_str)
    else:
         # 兄弟目录情况
         # 尝试找到它是哪个兄弟目录
         current_dir = os.getcwd()
         project_root = os.path.abspath(os.path.join(current_dir, ".."))
         matched_root = None
         if os.path.exists(project_root) and os.path.isdir(project_root):
                for item in os.listdir(project_root):
                    subdir = os.path.join(project_root, item)
                    if os.path.isdir(subdir) and not item.startswith('.') and subdir != current_dir:
                        # 检查 found_old_path 是否以 subdir 开头
                        if found_old_path.startswith(subdir):
                             # 确认 old_path_str 是否 match
                             candidate = os.path.join(subdir, old_path_str)
                             if os.path.abspath(candidate) == os.path.abspath(found_old_path):
                                 matched_root = subdir
                                 break
         
         if matched_root:
             abs_new_path = os.path.join(matched_root, new_path_str)
         else:
             # Fallback
             abs_new_path = os.path.join(os.path.dirname(found_old_path), os.path.basename(new_path_str))
             # 这只在同级重命名有效，但如果 new_path_str 是相对路径，可能会错
             # 让我们假设 new_path_str 是相对于 matched_root 的
             # 如果没找到 matched_root，这是一个异常情况
             logger.warn(f"无法确定文件根目录: {found_old_path}, fallback to dirname")
             # 尝试直接用 dirname
             # 如果 old="a/b.txt", new="a/c.txt", dirname(old)="/root/a", basename(new)="c.txt" -> "/root/a/c.txt". Correct.
             # 如果 old="a/b.txt", new="x/y.txt". dirname="/root/a". basename="y.txt" -> "/root/a/y.txt". Wrong.
             
             # 如果我们不能确定 root，我们可能无法正确处理跨目录重命名（在兄弟目录模式下）
             # 但通常我们只是重命名文件名
             pass

    # 确保目标目录存在
    os.makedirs(os.path.dirname(abs_new_path), exist_ok=True)

    try:
        os.rename(found_old_path, abs_new_path)
        logger.info(f"成功重命名文件: {found_old_path} -> {abs_new_path}")
    except Exception as e:
        logger.error(f"重命名文件失败: {str(e)}", exc_info=True)
        raise BusinessException(ErrorCode.INTERNAL_ERROR, message=f"重命名文件失败: {str(e)}")

    return success(data={"message": "重命名成功", "old_path": old_path_str, "new_path": new_path_str})

@router.post("/rename-folder")
async def rename_folder(request: FolderRenameRequest):
    """
    重命名文件夹接口
    """
    old_dir_str = request.old_dir
    new_dir_str = request.new_dir

    # 安全检查
    if not old_dir_str or '..' in old_dir_str or old_dir_str.startswith('/'):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="非法旧路径")
    if not new_dir_str or '..' in new_dir_str or new_dir_str.startswith('/'):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="非法新路径")

    # 构造绝对路径
    base_dir = os.path.abspath(settings.static_base_dir)
    abs_old_path = os.path.join(base_dir, old_dir_str)
    
    found_old_path = None
    
    # 1. 尝试在 static_base_dir 中查找
    if os.path.exists(abs_old_path) and os.path.isdir(abs_old_path):
        if os.path.abspath(abs_old_path).startswith(base_dir):
            found_old_path = abs_old_path

    # 2. 兄弟目录查找
    if not found_old_path:
        current_dir = os.getcwd()
        project_root = os.path.abspath(os.path.join(current_dir, ".."))
        try:
            if os.path.exists(project_root) and os.path.isdir(project_root):
                for item in os.listdir(project_root):
                    subdir = os.path.join(project_root, item)
                    if os.path.isdir(subdir) and not item.startswith('.') and subdir != current_dir:
                        candidate = os.path.join(subdir, old_dir_str)
                        if os.path.exists(candidate) and os.path.isdir(candidate):
                            if os.path.abspath(candidate).startswith(project_root):
                                found_old_path = candidate
                                logger.info(f"在兄弟目录中找到文件夹: {found_old_path}")
                                break
        except Exception as e:
            logger.warn(f"搜索兄弟目录失败: {e}")

    if not found_old_path:
        return success(data={"message": "原目录不存在", "path": old_dir_str})

    # 计算新目录绝对路径
    if found_old_path.startswith(base_dir):
         abs_new_path = os.path.join(base_dir, new_dir_str)
    else:
         # 兄弟目录
         current_dir = os.getcwd()
         project_root = os.path.abspath(os.path.join(current_dir, ".."))
         matched_root = None
         if os.path.exists(project_root) and os.path.isdir(project_root):
                for item in os.listdir(project_root):
                    subdir = os.path.join(project_root, item)
                    if os.path.isdir(subdir) and not item.startswith('.') and subdir != current_dir:
                        if found_old_path.startswith(subdir):
                             candidate = os.path.join(subdir, old_dir_str)
                             if os.path.abspath(candidate) == os.path.abspath(found_old_path):
                                 matched_root = subdir
                                 break
         if matched_root:
             abs_new_path = os.path.join(matched_root, new_dir_str)
         else:
             # Fallback
             abs_new_path = os.path.join(os.path.dirname(found_old_path), os.path.basename(new_dir_str))

    # 确保父目录存在
    os.makedirs(os.path.dirname(abs_new_path), exist_ok=True)

    try:
        os.rename(found_old_path, abs_new_path)
        logger.info(f"成功重命名文件夹: {found_old_path} -> {abs_new_path}")
    except Exception as e:
        logger.error(f"重命名文件夹失败: {str(e)}", exc_info=True)
        raise BusinessException(ErrorCode.INTERNAL_ERROR, message=f"重命名文件夹失败: {str(e)}")

    return success(data={"message": "重命名成功", "old_path": old_dir_str, "new_path": new_dir_str})

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
