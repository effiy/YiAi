"""
ID 转换工具 - 处理 ProjectFiles ID 与 Session ID 之间的转换

职责：
- 将文件路径转换为 Session ID
- 从 Session ID 解析出文件路径（优先使用映射表，备用方案通过文件系统查找）
- 支持区分目录和文件，确保路径解析的准确性
"""
import re
import os
import glob
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


def normalize_file_path_to_session_id(file_path: str, project_id: str) -> str:
    """
    将文件路径转换为 Session ID
    
    规则：
    - 使用双下划线 `__` 来标记目录分隔符（斜杠）
    - 单下划线用于文件名中的下划线
    - 格式：{projectId}__{dir1}__{dir2}__{filename}_{ext}
    
    例如：
    - knowledge/constructing/codereview/test.md -> knowledge__constructing__codereview__test_md
    - developer/process/process_claim_2025-12.md -> developer__process__process_claim_2025-12_md
    
    Args:
        file_path: 文件路径，如：knowledge/constructing/codereview/test.md 或 constructing/codereview/test.md
        project_id: 项目ID，如：knowledge
    
    Returns:
        Session ID，如：knowledge__constructing__codereview__test_md
    
    Raises:
        ValueError: 如果参数无效
    """
    if not file_path or not project_id:
        raise ValueError("file_path 和 project_id 是必需的")
    
    # 提取文件扩展名
    file_ext = ''
    if '.' in file_path:
        parts = file_path.rsplit('.', 1)
        path_without_ext = parts[0]
        file_ext = parts[1] if len(parts) > 1 else ''
    else:
        path_without_ext = file_path
    
    # 如果文件路径以项目ID开头，去除项目ID前缀（避免重复）
    # 例如：knowledge/constructing/test.md -> constructing/test.md
    if path_without_ext.startswith(f'{project_id}/'):
        path_without_ext = path_without_ext[len(project_id) + 1:]
    elif path_without_ext.startswith(project_id):
        # 处理没有斜杠的情况
        if len(path_without_ext) > len(project_id) and path_without_ext[len(project_id)] in ['/', '_']:
            path_without_ext = path_without_ext[len(project_id):].lstrip('/_')
    
    # 规范化路径：替换特殊字符为下划线，保留斜杠
    normalized = re.sub(r'[^a-zA-Z0-9/]', '_', path_without_ext)
    
    # 将斜杠替换为双下划线（用于区分目录分隔符）
    normalized = normalized.replace('/', '__')
    
    # 合并连续下划线（但保留双下划线）
    # 先保护双下划线
    normalized = normalized.replace('__', '\0\0')
    normalized = re.sub(r'_+', '_', normalized)
    normalized = normalized.replace('\0\0', '__')
    
    # 移除首尾下划线
    normalized = normalized.strip('_')
    
    # 如果有扩展名，添加到末尾（用单下划线分隔）
    if file_ext:
        normalized = f'{normalized}_{file_ext}'
    
    session_id = f'{project_id}__{normalized}'
    logger.debug(f"文件路径转换为 Session ID: {file_path} -> {session_id}")
    return session_id


def parse_session_id_to_file_path(
    session_id: str, 
    project_id: str,
    base_dir: Optional[str] = None
) -> Optional[str]:
    """
    从 Session ID 解析出文件路径（ProjectFiles ID）
    
    策略：
    1. 优先使用双下划线 `__` 作为目录分隔符（新格式）
    2. 如果没有双下划线，尝试通过文件系统查找（旧格式兼容）
    3. 通过文件系统验证找到正确的路径
    
    Args:
        session_id: Session ID，如：knowledge__constructing__codereview__test_md
        project_id: 项目ID，如：knowledge
        base_dir: 静态文件基础目录（用于文件系统查找），如：./static
    
    Returns:
        文件路径，如：knowledge/constructing/codereview/test.md，如果无法解析返回 None
    """
    if not session_id or not project_id:
        return None
    
    # 检查新格式（使用双下划线）
    if '__' in session_id:
        return _parse_new_format_session_id(session_id, project_id)
    
    # 旧格式兼容：尝试通过文件系统查找
    if base_dir:
        return _parse_old_format_session_id_with_filesystem(session_id, project_id, base_dir)
    
    # 如果没有 base_dir，使用旧的解析逻辑（可能不准确）
    return _parse_old_format_session_id(session_id, project_id)


def _parse_new_format_session_id(session_id: str, project_id: str) -> Optional[str]:
    """
    解析新格式的 Session ID（使用双下划线作为目录分隔符）
    
    格式：{projectId}__{dir1}__{dir2}__{filename}_{ext}
    例如：knowledge__constructing__codereview__test_md -> knowledge/constructing/codereview/test.md
    """
    prefix = f'{project_id}__'
    if not session_id.startswith(prefix):
        return None
    
    path_part = session_id[len(prefix):]
    
    # 处理扩展名（格式：path_md -> path.md）
    file_ext = ''
    if '_' in path_part:
        # 检查最后一部分是否是扩展名（通常是 1-5 个字符）
        parts = path_part.rsplit('_', 1)
        if len(parts) == 2 and len(parts[1]) <= 5 and parts[1].isalnum():
            path_part = parts[0]
            file_ext = parts[1]
    
    # 将双下划线替换为斜杠（目录分隔符）
    file_path = path_part.replace('__', '/')
    
    # 添加扩展名
    if file_ext:
        file_path = f'{file_path}.{file_ext}'
    elif not file_path.endswith('.md'):
        # 如果没有扩展名，默认添加 .md
        file_path += '.md'
    
    # 确保文件路径以项目ID开头
    if not file_path.startswith(f'{project_id}/'):
        file_path = f'{project_id}/{file_path}'
    
    logger.debug(f"新格式 Session ID 解析为文件路径: {session_id} -> {file_path}")
    return file_path


def _parse_old_format_session_id_with_filesystem(
    session_id: str, 
    project_id: str,
    base_dir: str
) -> Optional[str]:
    """
    通过文件系统查找解析旧格式的 Session ID
    
    策略：
    1. 尝试多种路径组合（将下划线转换为斜杠的不同方式）
    2. 通过文件系统验证找到存在的文件
    3. 支持区分目录和文件
    """
    prefix = f'{project_id}_'
    if not session_id.startswith(prefix):
        return None
    
    path_part = session_id[len(prefix):]
    
    # 处理扩展名
    file_ext = ''
    if '_' in path_part:
        parts = path_part.rsplit('_', 1)
        if len(parts) == 2 and len(parts[1]) <= 5 and parts[1].isalnum():
            path_part = parts[0]
            file_ext = parts[1]
    
    if not file_ext:
        file_ext = 'md'
    
    # 生成可能的路径组合
    # 例如：constructing_codereview_test -> 
    #   - constructing/codereview/test.md
    #   - constructing/codereview_test.md
    #   - constructing_codereview/test.md
    possible_paths = _generate_possible_paths(path_part, project_id, file_ext)
    
    # 通过文件系统验证
    for file_path in possible_paths:
        full_path = os.path.join(base_dir, file_path)
        if os.path.isfile(full_path):
            logger.debug(f"通过文件系统找到文件: {session_id} -> {file_path}")
            return file_path
    
    # 如果精确匹配都失败，尝试模糊匹配
    path_segments = path_part.split('_')
    if len(path_segments) >= 2:
        # 尝试不同的目录/文件名分割点
        for dir_end_idx in range(1, len(path_segments)):
            base_dir_segments = path_segments[:dir_end_idx]
            file_name_parts = path_segments[dir_end_idx:]
            
            if not base_dir_segments or not file_name_parts:
                continue
            
            base_dir_path = '/'.join(base_dir_segments)
            file_name_base = '_'.join(file_name_parts)
            
            # 在目录中查找匹配的文件
            search_pattern = os.path.join(
                base_dir, 
                project_id, 
                base_dir_path, 
                f"{file_name_base}*.{file_ext}"
            )
            matches = glob.glob(search_pattern)
            
            if matches:
                # 找到匹配的文件，返回相对路径
                for match in matches:
                    rel_path = os.path.relpath(match, base_dir)
                    if os.path.isfile(match):
                        logger.debug(f"通过模糊匹配找到文件: {session_id} -> {rel_path}")
                        return rel_path.replace('\\', '/')
    
    logger.warning(f"无法通过文件系统找到文件: {session_id}")
    return None


def _generate_possible_paths(path_part: str, project_id: str, file_ext: str) -> List[str]:
    """
    生成可能的文件路径组合
    
    例如：constructing_codereview_test
    生成：
    - knowledge/constructing/codereview/test.md
    - knowledge/constructing/codereview_test.md
    - knowledge/constructing_codereview/test.md
    """
    path_segments = path_part.split('_')
    possible_paths = []
    
    # 尝试不同的分割点，将下划线转换为斜杠
    # 从最深层到最浅层
    for i in range(1, len(path_segments) + 1):
        dir_part = '/'.join(path_segments[:i])
        file_part = '_'.join(path_segments[i:]) if i < len(path_segments) else ''
        
        if file_part:
            possible_paths.append(f"{project_id}/{dir_part}/{file_part}.{file_ext}")
        else:
            # 如果所有部分都是目录，最后一个作为文件名
            if dir_part:
                possible_paths.append(f"{project_id}/{dir_part}.{file_ext}")
    
    # 去重并保持顺序
    seen = set()
    unique_paths = []
    for path in possible_paths:
        if path not in seen:
            seen.add(path)
            unique_paths.append(path)
    
    return unique_paths


def _parse_old_format_session_id(session_id: str, project_id: str) -> Optional[str]:
    """
    解析旧格式的 Session ID（不使用文件系统，可能不准确）
    
    注意：此方法存在歧义，优先使用映射表或文件系统查找
    """
    prefix = f'{project_id}_'
    if not session_id.startswith(prefix):
        return None
    
    path_part = session_id[len(prefix):]
    
    # 处理扩展名
    file_ext = ''
    if '_' in path_part:
        parts = path_part.rsplit('_', 1)
        if len(parts) == 2 and len(parts[1]) <= 5 and parts[1].isalnum():
            path_part = parts[0]
            file_ext = parts[1]
    
    # 保持下划线不变（无法准确区分目录和文件）
    file_path = path_part
    
    # 添加扩展名
    if file_ext:
        file_path = f'{file_path}.{file_ext}'
    elif not file_path.endswith('.md'):
        file_path += '.md'
    
    # 确保文件路径以项目ID开头
    if not file_path.startswith(f'{project_id}/'):
        file_path = f'{project_id}/{file_path}'
    
    logger.debug(f"旧格式 Session ID 解析为文件路径（可能不准确）: {session_id} -> {file_path}")
    return file_path


def extract_project_id_from_file_path(file_path: str) -> Optional[str]:
    """
    从文件路径中提取项目ID
    
    Args:
        file_path: 文件路径，如：developer/process/process_claim_2025-12_xxx.md
    
    Returns:
        项目ID，如：developer，如果无法提取返回 None
    """
    if not file_path:
        return None
    
    # 文件路径格式：{projectId}/{filePath}
    parts = file_path.split('/', 1)
    if len(parts) >= 1:
        project_id = parts[0]
        return project_id
    
    return None


def is_aicr_session_id(session_id: str) -> bool:
    """
    判断是否是 AICR 相关的 Session ID（需要从文件系统读取 pageContent）
    
    判断规则：
    - Session ID 格式为 {projectId}__{filePath}（新格式，使用双下划线）
    - 或 {projectId}_{filePath}（旧格式，使用单下划线）
    - 包含至少一个下划线分隔的项目ID和文件路径
    
    Args:
        session_id: Session ID
    
    Returns:
        是否是 AICR 相关的 Session ID
    """
    if not session_id:
        return False
    
    # 检查新格式（双下划线）
    if '__' in session_id:
        parts = session_id.split('__', 1)
        if len(parts) == 2 and parts[0]:
            return True
    
    # 检查旧格式（单下划线）
    if '_' in session_id:
        parts = session_id.split('_', 2)
        if len(parts) >= 3:
            return True
        if len(parts) == 2 and parts[1].count('_') >= 1:
            return True
    
    return False


def normalize_project_file_id(file_id: str, project_id: str) -> str:
    """
    规范化 ProjectFile ID，确保格式统一
    
    规则：
    - 格式：{projectId}/{path/to/file.ext}
    - 确保以项目ID开头
    - 统一路径分隔符为斜杠
    - 去除重复的项目ID前缀
    
    Args:
        file_id: 文件ID，可能是：knowledge/constructing/test.md 或 constructing/test.md
        project_id: 项目ID，如：knowledge
    
    Returns:
        规范化后的文件ID，如：knowledge/constructing/test.md
    """
    if not file_id:
        return file_id
    
    # 统一路径分隔符
    normalized = file_id.replace('\\', '/').strip()
    
    # 去除开头的斜杠
    normalized = normalized.lstrip('/')
    
    # 分割路径部分
    parts = [p for p in normalized.split('/') if p]
    
    if not parts:
        return project_id
    
    # 去除重复的项目ID前缀
    while len(parts) > 1 and parts[0].lower() == project_id.lower() and parts[1].lower() == project_id.lower():
        parts = parts[1:]
    
    # 确保以项目ID开头
    if parts[0].lower() != project_id.lower():
        parts.insert(0, project_id)
    
    return '/'.join(parts)
