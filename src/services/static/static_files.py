"""静态文件管理
- 支持上传ZIP并安全解压到指定 static 目录
"""
import os
import zipfile
import logging
import shutil
import tempfile
from typing import Optional, List, Dict, Any
from fastapi import UploadFile
from core.config import settings
from core.error_codes import ErrorCode
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)

STATIC_BASE_DIR = os.path.abspath(settings.static_base_dir)
MAX_ZIP_SIZE = settings.static_max_zip_size

def _ensure_static_dir():
    """
    确保静态目录存在
    
    Raises:
        OSError: 创建目录失败时抛出
    """
    try:
        os.makedirs(STATIC_BASE_DIR, exist_ok=True)
    except Exception as e:
        logger.error(f"创建静态文件目录失败: {STATIC_BASE_DIR}, 错误: {e}", exc_info=True)
        raise

def _is_safe_path(path: str, base_dir: str) -> bool:
    """路径安全校验，防止越权写入"""
    try:
        normalized_path = os.path.normpath(path)
        normalized_base = os.path.normpath(base_dir)
        if '..' in normalized_path or normalized_path.startswith('/'):
            return False
        full_path = os.path.join(normalized_base, normalized_path)
        full_path = os.path.normpath(full_path)
        return full_path.startswith(normalized_base)
    except Exception:
        return False

def _decode_filename(filename):
    """兼容不同编码的ZIP文件名"""
    try:
        if isinstance(filename, bytes):
            return filename.decode('utf-8')
        try:
            return filename.encode('cp437').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return filename
    except Exception:
        return filename if isinstance(filename, str) else filename.decode('utf-8', errors='ignore')

def _resolve_target_dir(project_id: Optional[str]) -> str:
    """确定解压目标目录，验证路径安全"""
    if project_id:
        if not _is_safe_path(project_id, STATIC_BASE_DIR):
            raise BusinessException(ErrorCode.INVALID_PARAMS, message=f"无效的项目ID: {project_id}")
        return os.path.join(STATIC_BASE_DIR, project_id)
    return STATIC_BASE_DIR


def _find_common_root(file_list: list[str], project_id: Optional[str]) -> str:
    """检测ZIP内所有文件是否共享单一公共根目录"""
    first_level_dirs: set[str] = set()
    for file_path in file_list:
        if not file_path.endswith('/'):
            parts = file_path.replace('\\', '/').split('/')
            if parts and parts[0]:
                first_level_dirs.add(parts[0])
    if len(first_level_dirs) == 1:
        common_root = list(first_level_dirs)[0]
        if not project_id or common_root != project_id:
            return common_root + '/'
    return ''


def _extract_zip_entries(
    zip_ref: zipfile.ZipFile,
    strip_prefix: str,
    target_dir: str,
) -> tuple[list[str], list[str]]:
    """遍历ZIP条目，安全解压到目标目录"""
    extracted_files: list[str] = []
    extracted_dirs: list[str] = []
    for info in zip_ref.infolist():
        file_path = _decode_filename(info.filename)
        if file_path.endswith('/'):
            continue
        file_path = file_path.replace('\\', '/')
        normalized_path = file_path
        if strip_prefix and normalized_path.startswith(strip_prefix):
            normalized_path = normalized_path[len(strip_prefix):]
        if not normalized_path or not _is_safe_path(normalized_path, target_dir):
            continue
        full_target_path = os.path.join(target_dir, normalized_path)
        parent_dir = os.path.dirname(full_target_path)
        if parent_dir and parent_dir != target_dir:
            os.makedirs(parent_dir, exist_ok=True)
            if parent_dir not in extracted_dirs:
                extracted_dirs.append(parent_dir)
        try:
            with zip_ref.open(info) as source:
                with open(full_target_path, 'wb') as target:
                    shutil.copyfileobj(source, target)
            extracted_files.append(normalized_path)
        except Exception:
            logger.warning(f"Failed to extract file: {info.filename}", exc_info=True)
    return extracted_files, extracted_dirs


async def upload_and_unzip(file: UploadFile, project_id: Optional[str] = None) -> Dict[str, Any]:
    """上传ZIP并解压，自动剥离公共根目录"""
    _ensure_static_dir()
    if not file.filename or not file.filename.lower().endswith('.zip'):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="只支持ZIP格式文件")
    content = await file.read()
    if len(content) > MAX_ZIP_SIZE:
        raise BusinessException(ErrorCode.INVALID_PARAMS, message=f"ZIP文件大小超过限制: {MAX_ZIP_SIZE / 1024 / 1024}MB")

    target_dir = _resolve_target_dir(project_id)
    os.makedirs(target_dir, exist_ok=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
        temp_zip.write(content)
        temp_zip_path = temp_zip.name

    try:
        import sys
        zip_kwargs = {'metadata_encoding': 'utf-8'} if sys.version_info >= (3, 11) else {}
        with zipfile.ZipFile(temp_zip_path, 'r', **zip_kwargs) as zip_ref:
            file_list = [_decode_filename(info.filename) for info in zip_ref.infolist()]
            strip_prefix = _find_common_root(file_list, project_id) if file_list else ''
            extracted_files, extracted_dirs = _extract_zip_entries(zip_ref, strip_prefix, target_dir)
    finally:
        try:
            os.unlink(temp_zip_path)
        except Exception:
            logger.warning(f"Failed to clean up temp zip: {temp_zip_path}", exc_info=True)

    return {
        "filename": file.filename,
        "target_dir": target_dir,
        "extracted_files_count": len(extracted_files),
        "extracted_dirs_count": len(extracted_dirs),
        "project_id": project_id or os.path.basename(target_dir)
    }
