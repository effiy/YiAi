"""
维护相关 API
- 清理未引用的图片
- 清理 sessions 集合
"""
import os
import re
import logging
from pathlib import Path
from typing import Set, Dict, List, Any, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter
from core.error_codes import ErrorCode
from core.exceptions import BusinessException
from core.response import success
from core.config import settings
from services.maintenance.session_service import get_all_sessions, delete_session_by_key

logger = logging.getLogger(__name__)
router = APIRouter()

# 图片文件扩展名
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp', '.ico'}
MAX_UNUSED_IMAGE_DETAILS = 100  # limit detailed response to avoid OOM

# 图片引用模式
IMAGE_PATTERNS = [
    re.compile(r'!\[.*?\]\((.*?)\)', re.IGNORECASE),
    re.compile(r'<img[^>]+src=["\'](.*?)["\']', re.IGNORECASE),
    re.compile(r'(?:https?://[^/]+)?/static/([^\s"\'>]+)', re.IGNORECASE),
]


class CleanupRequest(BaseModel):
    dry_run: bool = Field(True, description="是否只预览不实际删除")
    cleanup_sessions: bool = Field(False, description="是否清理引用了不存在图片的 sessions")


def is_image_file(filepath: str) -> bool:
    """判断是否是图片文件"""
    ext = Path(filepath).suffix.lower()
    return ext in IMAGE_EXTENSIONS


def scan_static_images(static_dir: str) -> Set[str]:
    """扫描 static 目录下的所有图片文件"""
    static_path = Path(static_dir)
    if not static_path.exists():
        return set()

    image_paths = set()
    for root, _, files in os.walk(static_path):
        for file in files:
            if is_image_file(file):
                full_path = Path(root) / file
                rel_path = full_path.relative_to(static_path)
                image_paths.add(str(rel_path).replace('\\', '/'))

    return image_paths


def extract_referenced_images(text: str) -> Set[str]:
    """从文本中提取引用的图片路径"""
    referenced = set()

    for pattern in IMAGE_PATTERNS:
        matches = pattern.findall(text)
        for match in matches:
            url = match.strip()
            if not url:
                continue

            url = url.split('?')[0].split('#')[0]

            if url.startswith('http'):
                if '/static/' in url:
                    rel_path = url.split('/static/', 1)[1]
                    referenced.add(rel_path)
            elif url.startswith('/static/'):
                rel_path = url[len('/static/'):]
                referenced.add(rel_path)
            elif url.startswith('static/'):
                rel_path = url[len('static/'):]
                referenced.add(rel_path)
            else:
                referenced.add(url)

    return referenced


def _extract_refs_from_value(field_value: Any) -> Set[str]:
    """从任意嵌套结构的字段值中提取图片引用"""
    refs: Set[str] = set()
    if isinstance(field_value, str):
        refs.update(extract_referenced_images(field_value))
    elif isinstance(field_value, list):
        for item in field_value:
            refs.update(_extract_refs_from_value(item))
    elif isinstance(field_value, dict):
        for v in field_value.values():
            refs.update(_extract_refs_from_value(v))
    return refs


async def get_all_session_contents() -> tuple[Set[str], List[Dict[str, Any]]]:
    """从数据库 sessions 集合中获取所有引用的图片"""
    all_sessions = await get_all_sessions()
    referenced_images: Set[str] = set()
    for doc in all_sessions:
        for field_value in doc.values():
            referenced_images.update(_extract_refs_from_value(field_value))
    return referenced_images, all_sessions


def find_unused_images(static_images: Set[str], referenced_images: Set[str]) -> Set[str]:
    """找出未使用的图片"""
    unused = static_images - referenced_images
    referenced_lower = {p.lower() for p in referenced_images}
    still_unused = set()
    for img in unused:
        if img.lower() not in referenced_lower:
            still_unused.add(img)
    return still_unused


def delete_image_files(static_dir: str, unused_images: Set[str], dry_run: bool = True) -> tuple[int, int]:
    """删除未使用的图片文件，返回 (删除数量, 释放空间字节数)"""
    static_path = Path(static_dir)
    deleted_count = 0
    freed_space = 0

    for rel_path in unused_images:
        full_path = static_path / rel_path
        if full_path.exists():
            if not dry_run:
                try:
                    size = full_path.stat().st_size
                    full_path.unlink()
                    deleted_count += 1
                    freed_space += size
                    logger.info(f"Deleted: {full_path}")
                except Exception as e:
                    logger.error(f"Failed to delete {full_path}: {e}")
            else:
                try:
                    size = full_path.stat().st_size
                    freed_space += size
                    deleted_count += 1
                except (OSError, FileNotFoundError):
                    logger.debug(f"Stat failed for dry-run: {full_path}")

    return deleted_count, freed_space


async def cleanup_sessions_with_missing_images(
    static_dir: str,
    all_sessions: List[Dict[str, Any]],
    dry_run: bool = True
) -> int:
    """清理 sessions 集合中引用了不存在图片的文档"""
    static_path = Path(static_dir)
    cleaned_count = 0

    for session in all_sessions:
        session_key = session.get('key')
        if not session_key:
            continue

        has_missing_image = False

        for field_name, field_value in session.items():
            if field_name in ('_id', 'key'):
                continue
            refs = _extract_refs_from_value(field_value)
            for ref in refs:
                img_path = static_path / ref
                if not img_path.exists():
                    if ref.startswith('static/'):
                        img_path2 = static_path / ref[7:]
                        if img_path2.exists():
                            continue
                    has_missing_image = True
                    break

            if has_missing_image:
                break

        if has_missing_image:
            if not dry_run:
                try:
                    deleted = await delete_session_by_key(session_key)
                    if deleted > 0:
                        cleaned_count += 1
                        logger.info(f"Deleted session: {session_key}")
                except Exception as e:
                    logger.error(f"Failed to delete session {session_key}: {e}")
            else:
                cleaned_count += 1

    return cleaned_count


@router.post("/cleanup-unused-images", operation_id="cleanup_unused_images")
@router.post("/maintenance/cleanup-unused-images", operation_id="cleanup_unused_images_alt")
async def cleanup_unused_images(request: CleanupRequest):
    """
    清理未引用的图片

    Args:
        request: 清理请求参数
            - dry_run: 是否只预览不实际删除 (默认: true)
            - cleanup_sessions: 是否清理引用了不存在图片的 sessions (默认: false)

    Returns:
        清理结果统计
    """
    static_dir = os.path.abspath(settings.static_base_dir)
    logger.info(f"Static directory: {static_dir}")
    logger.info(f"Dry run: {request.dry_run}")
    logger.info(f"Cleanup sessions: {request.cleanup_sessions}")

    # 1. 扫描静态图片
    static_images = scan_static_images(static_dir)

    # 2. 获取数据库中引用的图片
    referenced_images, all_sessions = await get_all_session_contents()

    # 3. 找出未使用的图片
    unused_images = find_unused_images(static_images, referenced_images)

    # 4. 计算统计信息
    total_size = 0
    unused_list = []
    for img in sorted(unused_images):
        img_path = Path(static_dir) / img
        if img_path.exists():
            size = img_path.stat().st_size
            total_size += size
            unused_list.append({
                "path": img,
                "size_bytes": size,
                "size_kb": round(size / 1024, 2)
            })

    # 5. 删除未使用的图片
    deleted_count, freed_space = delete_image_files(static_dir, unused_images, dry_run=request.dry_run)

    # 6. 清理引用了不存在图片的 sessions
    cleaned_sessions = 0
    if request.cleanup_sessions:
        cleaned_sessions = await cleanup_sessions_with_missing_images(
            static_dir, all_sessions, dry_run=request.dry_run
        )

    return success(data={
        "dry_run": request.dry_run,
        "summary": {
            "total_images_found": len(static_images),
            "total_images_referenced": len(referenced_images),
            "unused_images_count": len(unused_images),
            "unused_images_size_bytes": total_size,
            "unused_images_size_mb": round(total_size / 1024 / 1024, 2),
            "deleted_count": deleted_count,
            "freed_space_bytes": freed_space,
            "freed_space_mb": round(freed_space / 1024 / 1024, 2),
            "cleaned_sessions_count": cleaned_sessions
        },
        "unused_images": unused_list[:MAX_UNUSED_IMAGE_DETAILS]
    })
