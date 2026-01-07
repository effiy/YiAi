"""工具函数"""
import re
import json
import hashlib
import random
import string
import math
from typing import Union, Any, List, Dict, Optional, Generator
from datetime import datetime, timezone

# --- 文本处理 ---

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

def clean_text(text: str) -> str:
    """
    清理文本：去除首尾空白，将连续空白字符替换为单个空格
    """
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def truncate_text(text: str, length: int, ellipsis: str = "...") -> str:
    """
    截断文本，如果超出长度则添加省略号
    """
    if not text or len(text) <= length:
        return text
    return text[:length] + ellipsis

def generate_md5(text: str) -> str:
    """生成字符串的 MD5 哈希"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def generate_random_string(length: int = 8, chars: str = string.ascii_letters + string.digits) -> str:
    """生成指定长度的随机字符串"""
    return ''.join(random.choice(chars) for _ in range(length))

def extract_json_from_text(text: str) -> Optional[Union[Dict, List]]:
    """
    尝试从文本中提取并解析 JSON
    支持提取 markdown 代码块中的 JSON (```json ... ```)
    """
    if not text:
        return None
        
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取 Markdown 代码块
    pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
    # 尝试查找第一个 { 或 [ 到最后一个 } 或 ]
    try:
        start_idx = -1
        end_idx = -1
        
        # 查找可能的开始位置
        first_brace = text.find('{')
        first_bracket = text.find('[')
        
        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            start_idx = first_brace
        elif first_bracket != -1:
            start_idx = first_bracket
            
        # 查找可能的结束位置
        last_brace = text.rfind('}')
        last_bracket = text.rfind(']')
        
        if last_brace != -1 and (last_bracket == -1 or last_brace > last_bracket):
            end_idx = last_brace
        elif last_bracket != -1:
            end_idx = last_bracket
            
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx:end_idx+1]
            return json.loads(json_str)
    except Exception:
        pass
        
    return None

# --- 时间与日期 ---

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

# --- 数字与文件 ---

def is_number(value: Any) -> bool:
    """验证值是否为数字"""
    if value is None:
        return False
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

def format_file_size(size_in_bytes: int) -> str:
    """
    将字节大小转换为人类可读格式 (KB, MB, GB)
    """
    if size_in_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_in_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_in_bytes / p, 2)
    return f"{s} {size_name[i]}"

# --- 集合处理 ---

def chunk_list(lst: List[Any], size: int) -> Generator[List[Any], None, None]:
    """
    将列表分割为指定大小的块
    """
    for i in range(0, len(lst), size):
        yield lst[i:i + size]
