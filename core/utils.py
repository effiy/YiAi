"""工具函数"""
from typing import Union

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
