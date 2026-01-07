import logging
import uuid
import feedparser
import aiohttp
from typing import Dict, Any, Optional
from fastapi import HTTPException
from core.database import db
from core.config import settings
from core.utils import get_current_time

logger = logging.getLogger(__name__)

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
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=400,
                        detail=f"无法获取 RSS 源，HTTP 状态码: {response.status}"
                    )
                content = await response.text()
                feed = feedparser.parse(content)

                if feed.bozo and feed.bozo_exception:
                    logger.warning(f"RSS 解析警告: {feed.bozo_exception}")

                return feed
    except aiohttp.ClientError as e:
        logger.error(f"获取 RSS 源失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"获取 RSS 源失败: {str(e)}")
    except Exception as e:
        logger.error(f"解析 RSS 源失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"解析 RSS 源失败: {str(e)}")

async def process_feed_from_url(url: str, name: Optional[str] = None) -> Dict[str, Any]:
    """
    获取、解析并保存 RSS 源数据 (核心业务逻辑)
    
    Returns:
        Dict: 统计结果 {saved_count, updated_count, source_name, total_items, url, success, error}
    """
    try:
        # 确保数据库已初始化
        await db.initialize()

        # 获取并解析 RSS 源
        feed = await fetch_rss_feed(url)

        # 获取源名称（优先使用传入的 name，否则使用 feed 的 title）
        source_name = name or feed.feed.get('title', '未知源')
        tags = [source_name] if source_name else []

        # 准备要存储的数据
        items_to_save = []
        current_time = get_current_time()

        # 解析每个条目
        for entry in feed.entries:
            item_link = entry.get('link', '')
            if not item_link:
                continue  # 跳过没有链接的条目

            item_data = {
                'title': entry.get('title', ''),
                'link': item_link,
                'description': entry.get('description', '') or entry.get('summary', ''),
                'tags': tags,
                'source_name': source_name,
                'source_url': url,
                'published': entry.get('published', ''),
                'published_parsed': str(entry.get('published_parsed', '')) if entry.get('published_parsed') else '',
                'createdTime': current_time,
                'updatedTime': current_time
            }

            # 如果有作者信息，也保存
            if entry.get('author'):
                item_data['author'] = entry.get('author')

            # 如果有内容，也保存
            if entry.get('content'):
                content_list = entry.get('content', [])
                if content_list and len(content_list) > 0:
                    item_data['content'] = content_list[0].get('value', '')

            items_to_save.append(item_data)

        # 批量存入 MongoDB
        collection = db.db[settings.collection_rss]
        saved_count = 0
        updated_count = 0

        for item in items_to_save:
            # 检查是否已存在
            existing_item = await collection.find_one({'link': item['link']})

            if existing_item:
                # 更新
                item['key'] = existing_item.get('key', str(uuid.uuid4()))
                item['createdTime'] = existing_item.get('createdTime', current_time)
                result = await collection.update_one(
                    {'link': item['link']},
                    {'$set': item}
                )
                if result.modified_count > 0:
                    updated_count += 1
            else:
                # 新增
                item['key'] = str(uuid.uuid4())
                await collection.insert_one(item)
                saved_count += 1

        return {
            'url': url,
            'source_name': source_name,
            'success': True,
            'saved_count': saved_count,
            'updated_count': updated_count,
            'total_items': len(items_to_save)
        }
    except Exception as e:
        logger.error(f"处理 RSS 源 {url} 失败: {str(e)}")
        return {
            'url': url,
            'source_name': name or url,
            'success': False,
            'error': str(e)
        }

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
        "source": result.get('source_name', 'Unknown'),
        "saved_count": result.get('saved_count', 0),
        "updated_count": result.get('updated_count', 0)
    }
