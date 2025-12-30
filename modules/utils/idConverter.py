"""
ID 转换工具 - 处理 ProjectFiles ID 与 Session ID 之间的转换

职责：
- 将文件路径转换为 Session ID
- 从 Session ID 解析出文件路径（备用方案，优先使用映射表）
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def normalize_file_path_to_session_id(file_path: str, project_id: str) -> str:
    """
    将文件路径转换为 Session ID
    
    Args:
        file_path: 文件路径，如：developer/process/process_claim_2025-12_xxx.md
        project_id: 项目ID，如：developer
    
    Returns:
        Session ID，如：aicr_developer_process_process_claim_2025-12_xxx_md
    
    Raises:
        ValueError: 如果参数无效
    """
    if not file_path or not project_id:
        raise ValueError("file_path 和 project_id 是必需的")
    
    # 移除文件扩展名（保留在路径中用于反向解析）
    path_without_ext = file_path.rsplit('.', 1)[0] if '.' in file_path else file_path
    
    # 替换特殊字符为下划线（保留斜杠用于路径识别）
    normalized = re.sub(r'[^a-zA-Z0-9/]', '_', path_without_ext)
    
    # 将斜杠替换为下划线
    normalized = normalized.replace('/', '_')
    
    # 合并连续下划线
    normalized = re.sub(r'_+', '_', normalized)
    
    # 移除首尾下划线
    normalized = normalized.strip('_')
    
    session_id = f'aicr_{project_id}_{normalized}'
    logger.debug(f"文件路径转换为 Session ID: {file_path} -> {session_id}")
    return session_id


def parse_session_id_to_file_path(session_id: str, project_id: str) -> Optional[str]:
    """
    从 Session ID 解析出文件路径（ProjectFiles ID）
    注意：此方法存在歧义，优先使用映射表进行关联
    
    Args:
        session_id: Session ID，如：aicr_developer_process_process_claim_2025-12_xxx_md
        project_id: 项目ID，如：developer
    
    Returns:
        文件路径，如：developer/process/process_claim_2025-12_xxx.md，如果无法解析返回 None
    """
    if not session_id or not project_id:
        return None
    
    prefix = f'aicr_{project_id}_'
    if not session_id.startswith(prefix):
        return None
    
    path_part = session_id[len(prefix):]
    
    # 将下划线还原为斜杠
    file_path = path_part.replace('_', '/')
    
    # 添加 .md 扩展名（如果原路径有扩展名）
    if not file_path.endswith('.md'):
        file_path += '.md'
    
    # 确保文件路径以项目ID开头
    if not file_path.startswith(f'{project_id}/'):
        file_path = f'{project_id}/{file_path}'
    
    logger.debug(f"Session ID 解析为文件路径: {session_id} -> {file_path}")
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
    判断是否是 AICR 相关的 Session ID
    
    Args:
        session_id: Session ID
    
    Returns:
        是否是 AICR 相关的 Session ID
    """
    return session_id and session_id.startswith('aicr_')

