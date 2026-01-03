"""
静态文件管理路由 - 处理静态文件的上传、解压等操作
"""
import os
import zipfile
import logging
import shutil
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from router.utils import create_response, handle_error

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/static",
    tags=["Static Files"],
    responses={404: {"description": "未找到"}},
)

# 静态文件基础目录
STATIC_BASE_DIR = os.path.abspath("./static")
MAX_ZIP_SIZE = 100 * 1024 * 1024  # 100MB


def _ensure_static_dir():
    """确保static目录存在"""
    try:
        os.makedirs(STATIC_BASE_DIR, exist_ok=True)
        logger.info(f"静态文件目录已准备: {STATIC_BASE_DIR}")
    except Exception as e:
        logger.error(f"创建静态文件目录失败: {STATIC_BASE_DIR}, 错误: {e}", exc_info=True)
        raise


def _is_safe_path(path: str, base_dir: str) -> bool:
    """
    检查路径是否安全（防止路径遍历攻击）

    Args:
        path: 要检查的路径
        base_dir: 基础目录

    Returns:
        如果路径安全返回True，否则返回False
    """
    try:
        # 规范化路径
        normalized_path = os.path.normpath(path)
        normalized_base = os.path.normpath(base_dir)

        # 检查是否包含路径遍历
        if '..' in normalized_path or normalized_path.startswith('/'):
            return False

        # 检查是否在基础目录内
        full_path = os.path.join(normalized_base, normalized_path)
        full_path = os.path.normpath(full_path)

        return full_path.startswith(normalized_base)
    except Exception:
        return False


@router.post("/upload-zip")
async def upload_zip_to_static(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None)
) -> JSONResponse:
    """
    上传ZIP文件并解压到static目录

    功能：
    - 接收ZIP文件
    - 解压到static目录
    - 如果指定了project_id，则解压到static/{project_id}目录
    - 覆盖已存在的文件和目录

    Args:
        file: ZIP文件
        project_id: 项目ID（可选），如果提供，文件将解压到static/{project_id}目录

    Returns:
        上传和解压结果
    """
    try:
        _ensure_static_dir()

        # 验证文件类型
        if not file.filename or not file.filename.lower().endswith('.zip'):
            raise HTTPException(
                status_code=400,
                detail="只支持ZIP格式文件"
            )

        # 读取文件内容
        content = await file.read()

        # 检查文件大小
        if len(content) > MAX_ZIP_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"ZIP文件大小超过限制: {MAX_ZIP_SIZE / 1024 / 1024}MB"
            )

        # 确定目标目录
        if project_id:
            # 验证project_id是否安全
            if not _is_safe_path(project_id, STATIC_BASE_DIR):
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的项目ID: {project_id}"
                )
            target_dir = STATIC_BASE_DIR
        else:
            # 如果没有指定project_id，从ZIP文件名解析
            zip_name = os.path.splitext(file.filename)[0]
            if zip_name and _is_safe_path(zip_name, STATIC_BASE_DIR):
                target_dir = os.path.join(STATIC_BASE_DIR, zip_name)
            else:
                # 默认解压到static根目录
                target_dir = STATIC_BASE_DIR

        # 创建目标目录
        os.makedirs(target_dir, exist_ok=True)

        # 解压ZIP文件
        extracted_files = []
        extracted_dirs = []

        # 将文件内容写入临时ZIP文件
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
            temp_zip.write(content)
            temp_zip_path = temp_zip.name

        try:
            # 处理中文文件名的辅助函数
            def decode_filename(filename):
                """解码ZIP文件中的文件名，支持中文"""
                try:
                    # Python 3.11+ 支持 metadata_encoding 参数，但这里我们需要手动处理
                    # 尝试UTF-8解码（现代ZIP文件通常使用UTF-8）
                    if isinstance(filename, bytes):
                        return filename.decode('utf-8')
                    # 如果已经是字符串，尝试从CP437转换到UTF-8
                    try:
                        return filename.encode('cp437').decode('utf-8')
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        # 如果转换失败，可能已经是UTF-8，直接返回
                        return filename
                except Exception:
                    # 如果所有尝试都失败，返回原始值
                    return filename if isinstance(filename, str) else filename.decode('utf-8', errors='ignore')

            # 打开ZIP文件
            # Python 3.11+ 支持 metadata_encoding 参数
            import sys
            if sys.version_info >= (3, 11):
                zip_ref = zipfile.ZipFile(temp_zip_path, 'r', metadata_encoding='utf-8')
            else:
                zip_ref = zipfile.ZipFile(temp_zip_path, 'r')

            with zip_ref:
                # 获取所有文件列表，处理中文编码
                file_list = []
                for info in zip_ref.infolist():
                    file_path = decode_filename(info.filename)
                    file_list.append(file_path)

                # 检测是否需要剥离共同根目录
                # 改进的检测逻辑：只有当所有文件都在同一个根目录下，且该根目录不是项目ID时才剥离
                strip_prefix = ''
                if file_list:
                    first_level_dirs = set()
                    for file_path in file_list:
                        if not file_path.endswith('/'):  # 忽略目录项
                            # 规范化路径分隔符
                            normalized = file_path.replace('\\', '/')
                            parts = normalized.split('/')
                            if parts and parts[0]:
                                first_level_dirs.add(parts[0])

                    # 如果所有文件都在同一个根目录下，且该根目录不是项目ID，则剥离
                    if len(first_level_dirs) == 1:
                        common_root = list(first_level_dirs)[0]
                        # 如果共同根目录与项目ID相同，不剥离（避免重复）
                        if not project_id or common_root != project_id:
                            strip_prefix = common_root + '/'
                            logger.info(f"检测到共同根目录，将剥离: {strip_prefix}")

                # 解压文件
                for info in zip_ref.infolist():
                    # 获取正确的文件名（处理中文编码）
                    file_path = decode_filename(info.filename)

                    # 跳过目录项
                    if file_path.endswith('/'):
                        continue

                    # 规范化路径分隔符
                    file_path = file_path.replace('\\', '/')

                    # 剥离共同根目录
                    normalized_path = file_path
                    if strip_prefix and normalized_path.startswith(strip_prefix):
                        normalized_path = normalized_path[len(strip_prefix):]

                    # 跳过空路径
                    if not normalized_path:
                        continue

                    # 验证路径安全
                    if not _is_safe_path(normalized_path, target_dir):
                        logger.warning(f"跳过不安全的路径: {file_path}")
                        continue

                    # 构建完整的目标路径（确保使用正确的编码）
                    full_target_path = os.path.join(target_dir, normalized_path)

                    # 确保父目录存在
                    parent_dir = os.path.dirname(full_target_path)
                    if parent_dir and parent_dir != target_dir:
                        os.makedirs(parent_dir, exist_ok=True)
                        if parent_dir not in extracted_dirs:
                            extracted_dirs.append(parent_dir)

                    # 解压文件
                    try:
                        with zip_ref.open(info) as source:
                            with open(full_target_path, 'wb') as target:
                                shutil.copyfileobj(source, target)

                        extracted_files.append(normalized_path)
                        logger.debug(f"解压文件: {normalized_path}")
                    except Exception as e:
                        logger.error(f"解压文件失败: {file_path}, 错误: {e}")
                        continue

        finally:
            # 清理临时文件
            try:
                os.unlink(temp_zip_path)
            except Exception:
                pass

        logger.info(f"ZIP文件解压成功: {file.filename}, 目标目录: {target_dir}, 文件数: {len(extracted_files)}")

        return create_response(
            code=200,
            message="ZIP文件上传并解压成功",
            data={
                "filename": file.filename,
                "target_dir": target_dir,
                "extracted_files_count": len(extracted_files),
                "extracted_dirs_count": len(extracted_dirs),
                "project_id": project_id or os.path.basename(target_dir)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传并解压ZIP文件失败: {str(e)}", exc_info=True)
        return handle_error(e, 500)

