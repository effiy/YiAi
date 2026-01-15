"""静态文件管理
- 支持上传ZIP并安全解压到指定 static 目录
"""
import os
import zipfile
import logging
import shutil
import tempfile
from typing import Optional, List, Dict, Any
from fastapi import UploadFile, HTTPException
from core.settings import settings

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

async def upload_and_unzip(file: UploadFile, project_id: Optional[str] = None) -> Dict[str, Any]:
    """
    上传ZIP并解压，自动剥离公共根目录
    
    Args:
        file: 上传的文件
        project_id: 项目ID (可选)
        
    Returns:
        Dict[str, Any]: 处理结果
            - filename (str): 文件名
            - target_dir (str): 目标目录
            - extracted_files_count (int): 解压文件数
            - extracted_dirs_count (int): 解压目录数
            - project_id (str): 项目ID
            
    Raises:
        HTTPException: 文件格式错误、大小超限或路径不安全
    """
    _ensure_static_dir()
    if not file.filename or not file.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="只支持ZIP格式文件")
    content = await file.read()
    if len(content) > MAX_ZIP_SIZE:
        raise HTTPException(status_code=400, detail=f"ZIP文件大小超过限制: {MAX_ZIP_SIZE / 1024 / 1024}MB")

    if project_id:
        if not _is_safe_path(project_id, STATIC_BASE_DIR):
            raise HTTPException(status_code=400, detail=f"无效的项目ID: {project_id}")
        target_dir = os.path.join(STATIC_BASE_DIR, project_id)
    else:
        zip_name = os.path.splitext(file.filename)[0]
        if zip_name and _is_safe_path(zip_name, STATIC_BASE_DIR):
            target_dir = os.path.join(STATIC_BASE_DIR, zip_name)
        else:
            target_dir = STATIC_BASE_DIR

    os.makedirs(target_dir, exist_ok=True)
    extracted_files = []
    extracted_dirs = []

    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
        temp_zip.write(content)
        temp_zip_path = temp_zip.name

    try:
        import sys
        if sys.version_info >= (3, 11):
            zip_ref = zipfile.ZipFile(temp_zip_path, 'r', metadata_encoding='utf-8')
        else:
            zip_ref = zipfile.ZipFile(temp_zip_path, 'r')

        with zip_ref:
            file_list = []
            for info in zip_ref.infolist():
                file_path = _decode_filename(info.filename)
                file_list.append(file_path)

            strip_prefix = ''
            if file_list:
                first_level_dirs = set()
                for file_path in file_list:
                    if not file_path.endswith('/'):
                        normalized = file_path.replace('\\', '/')
                        parts = normalized.split('/')
                        if parts and parts[0]:
                            first_level_dirs.add(parts[0])
                if len(first_level_dirs) == 1:
                    common_root = list(first_level_dirs)[0]
                    if not project_id or common_root != project_id:
                        strip_prefix = common_root + '/'

            for info in zip_ref.infolist():
                file_path = _decode_filename(info.filename)
                if file_path.endswith('/'):
                    continue
                file_path = file_path.replace('\\', '/')
                normalized_path = file_path
                if strip_prefix and normalized_path.startswith(strip_prefix):
                    normalized_path = normalized_path[len(strip_prefix):]
                if not normalized_path:
                    continue
                if not _is_safe_path(normalized_path, target_dir):
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
                    continue
    finally:
        try:
            os.unlink(temp_zip_path)
        except Exception:
            pass

    return {
        "filename": file.filename,
        "target_dir": target_dir,
        "extracted_files_count": len(extracted_files),
        "extracted_dirs_count": len(extracted_dirs),
        "project_id": project_id or os.path.basename(target_dir)
    }
