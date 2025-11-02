"""会话管理工具函数"""
import hashlib
from urllib.parse import urlparse


def normalize_session_id(session_id: str) -> str:
    """
    规范化 session_id：如果 session_id 是 URL 格式，则进行 MD5 处理
    
    Args:
        session_id: 原始 session_id
    
    Returns:
        规范化后的 session_id
    """
    if not session_id:
        return session_id
    
    # 检查是否是 URL 格式
    try:
        result = urlparse(session_id)
        # 如果包含 scheme 或 netloc，认为是 URL 格式
        if result.scheme or result.netloc:
            # 使用 MD5 处理 URL
            md5_hash = hashlib.md5(session_id.encode('utf-8')).hexdigest()
            return md5_hash
    except Exception:
        # 如果解析失败，可能不是标准 URL，直接返回原值
        pass
    
    return session_id

