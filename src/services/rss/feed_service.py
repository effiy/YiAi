import logging
import uuid
import feedparser
import aiohttp
import gc
from typing import Dict, Any, Optional
from core.database import db
from core.config import settings
from core.utils import get_current_time
from core.error_codes import ErrorCode
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)

RSS_CHUNK_SIZE = 8192  # bytes per chunk when streaming RSS feed

async def fetch_rss_feed(url: str) -> feedparser.FeedParserDict:
    """
    获取并解析 RSS 源内容
    
    Args:
        url: RSS 源地址
        
    Returns:
        feedparser.FeedParserDict: 解析后的 RSS 数据
        
    Raises:
        HTTPException: 获取或解析失败时抛出
    """
    # 限制最大 RSS 大小为 10MB，防止内存溢出
    MAX_RSS_SIZE = 10 * 1024 * 1024
    
    try:
        async with aiohttp.ClientSession() as session:
            # 增加超时时间到 60秒
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status != 200:
                    raise BusinessException(
                        ErrorCode.INVALID_PARAMS,
                        message=f"无法获取 RSS 源，HTTP 状态码: {response.status}"
                    )
                
                # 检查 Content-Length
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > MAX_RSS_SIZE:
                    raise BusinessException(
                        ErrorCode.INVALID_PARAMS,
                        message=f"RSS 源过大 (Content-Length: {content_length})，超过限制 {MAX_RSS_SIZE} 字节"
                    )

                # 流式读取并限制大小
                content = bytearray()
                async for chunk in response.content.iter_chunked(RSS_CHUNK_SIZE):
                    content.extend(chunk)
                    if len(content) > MAX_RSS_SIZE:
                        raise BusinessException(
                            ErrorCode.INVALID_PARAMS,
                            message=f"RSS 源实际内容过大，超过限制 {MAX_RSS_SIZE} 字节"
                        )
                
                feed = feedparser.parse(bytes(content))

                if feed.bozo and feed.bozo_exception:
                    logger.warning(f"RSS 解析警告: {feed.bozo_exception}")

                return feed
    except aiohttp.ClientError as e:
        logger.error(f"获取 RSS 源失败: {str(e)}")
        raise BusinessException(ErrorCode.INVALID_PARAMS, message=f"获取 RSS 源失败: {str(e)}")
    except Exception as e:
        logger.error(f"解析 RSS 源失败: {str(e)}")
        raise BusinessException(ErrorCode.INTERNAL_ERROR, message=f"解析 RSS 源失败: {str(e)}")

def _build_entry_data(entry, source_name: str, tags: list[str], url: str, current_time: str) -> Dict[str, Any]:
    """从 RSS entry 构建入库数据"""
    item_data = {
        'title': entry.get('title', ''),
        'link': entry.get('link', ''),
        'description': entry.get('description', '') or entry.get('summary', ''),
        'tags': tags,
        'source_name': source_name,
        'source_url': url,
        'published': entry.get('published', ''),
        'published_parsed': str(entry.get('published_parsed', '')) if entry.get('published_parsed') else '',
        'createdTime': current_time,
        'updatedTime': current_time,
    }
    if entry.get('author'):
        item_data['author'] = entry.get('author')
    content_list = entry.get('content', [])
    if content_list:
        item_data['content'] = content_list[0].get('value', '')
    return item_data


async def _save_or_update_entry(collection, item_data: Dict[str, Any], current_time: str) -> int:
    """保存或更新单条RSS条目，返回 added=1 或 updated=1"""
    existing_item = await collection.find_one({'link': item_data['link']})
    if existing_item:
        item_data['key'] = existing_item.get('key', str(uuid.uuid4()))
        item_data['createdTime'] = existing_item.get('createdTime', current_time)
        result = await collection.update_one({'link': item_data['link']}, {'$set': item_data})
        return 0, 1 if result.modified_count > 0 else 0
    else:
        item_data['key'] = str(uuid.uuid4())
        await collection.insert_one(item_data)
        return 1, 0


async def process_feed_from_url(url: str, name: Optional[str] = None) -> Dict[str, Any]:
    """获取、解析并保存 RSS 源数据"""
    try:
        await db.initialize()
        feed = await fetch_rss_feed(url)
        source_name = name or feed.feed.get('title', '未知源')
        tags = [source_name] if source_name else []
        current_time = get_current_time()
        collection = db.db[settings.collection_rss]

        saved_count = updated_count = total_items = 0
        for entry in feed.entries:
            if not entry.get('link'):
                continue
            total_items += 1
            item_data = _build_entry_data(entry, source_name, tags, url, current_time)
            added, updated = await _save_or_update_entry(collection, item_data, current_time)
            saved_count += added
            updated_count += updated

        del feed
        gc.collect()
        return {
            'url': url, 'source_name': source_name, 'success': True,
            'saved_count': saved_count, 'updated_count': updated_count, 'total_items': total_items,
        }
    except Exception as e:
        logger.error(f"处理 RSS 源 {url} 失败: {str(e)}")
        return {'url': url, 'source_name': name or url, 'success': False, 'error': str(e)}

async def parse_feed(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析 RSS 源并存入 MongoDB (API 接口)
    
    Args:
        params: 参数字典
            - url (str): RSS 源地址
            - name (str, optional): 源名称
            
    Returns:
        Dict[str, Any]: 解析结果统计
    """
    url = params.get("url")
    if not url:
        raise ValueError("URL is required")
    
    name = params.get("name")
    
    logger.info(f"开始解析 RSS 源: {url}")
    result = await process_feed_from_url(url, name)
    
    if not result.get('success'):
        # 如果是 API 调用，可能希望抛出异常或返回错误信息
        # 这里为了保持 API 兼容性，我们返回部分信息，但 parse_feed 原始设计是返回 success bool
        pass
        
    return {
        "success": result.get('success', False),
        "url": url,
        "source": result.get('source_name', 'Unknown'),
        "saved_count": result.get('saved_count', 0),
        "updated_count": result.get('updated_count', 0),
        "total_items": result.get('total_items', 0),
        "error": result.get('error')
    }
