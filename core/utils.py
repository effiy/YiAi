"""工具函数"""
from typing import Union, Any
from datetime import datetime, timezone

def estimate_tokens(text: Union[str, bytes]) -> int:
    """
    估算文本的 Token 数量 (简易版)
    ASCII 字符 (如英文) 约 4 个字符为 1 token (0.25)
    非 ASCII 字符 (如中文) 计为 1 token
    """
    if not isinstance(text, str):
        return 0
        
    token_count = 0
    for char in text:
        if ord(char) > 127: 
            token_count += 1
        else:
            token_count += 0.25
            
    return int(token_count)

def get_current_time() -> str:
    """获取当前 UTC 时间字符串 (ISO 8601 format with Z)"""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def is_valid_date(date_str: str) -> bool:
    """验证日期字符串格式是否有效 (YYYY-MM-DD)"""
    if not isinstance(date_str, str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def is_number(value: Any) -> bool:
    """验证值是否为数字"""
    if value is None:
        return False
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False
