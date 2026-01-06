import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from core.database import db
from core.config import settings
from services.rss.rss_scheduler import fetch_rss_feed

logger = logging.getLogger(__name__)

async def parse_feed(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析 RSS 源并存入 MongoDB
    
    Args:
        params: 参数字典
            - url (str): RSS 源地址
            - name (str, optional): 源名称
            
    Returns:
        Dict[str, Any]: 解析结果统计
            - success (bool): 是否成功
            - source (str): 源名称
            - saved_count (int): 新增条目数
            - updated_count (int): 更新条目数
            
    Raises:
        ValueError: URL 未提供

    Example:
        GET /?module_name=services.rss.feed_service&method_name=parse_feed&parameters={"url": "https://example.com/rss.xml"}
    """
    url = params.get("url")
    if not url:
        raise ValueError("URL is required")
    
    name = params.get("name")
    
    # 确保数据库已初始化
    await db.initialize()

    # 获取并解析 RSS 源
    logger.info(f"开始解析 RSS 源: {url}")
    feed = await fetch_rss_feed(url)

    # 获取源名称（优先使用传入的 name，否则使用 feed 的 title）
    source_name = name or feed.feed.get('title', '未知源')

    # 提取标签（使用源名称作为标签）
    tags = [source_name] if source_name else []

    # 准备要存储的数据
    items_to_save = []
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # 解析每个条目
    for entry in feed.entries:
        item_link = entry.get('link', '')
        if not item_link:
            continue  # 跳过没有链接的条目

        item_data = {
            'title': entry.get('title', ''),
            'link': item_link,
            'description': entry.get('description', '') or entry.get('summary', ''),
            'tags': tags,  # 将源名称作为标签
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

    # 批量存入 MongoDB（使用 link 作为唯一标识，避免重复）
    collection = db.db[settings.collection_rss]
    saved_count = 0
    updated_count = 0

    for item in items_to_save:
        # 检查是否已存在（使用 link 作为唯一标识）
        existing_item = await collection.find_one({'link': item['link']})

        if existing_item:
            # 如果已存在，更新数据（保留原有的 key 和 createdTime）
            item['key'] = existing_item.get('key', str(uuid.uuid4()))
            item['createdTime'] = existing_item.get('createdTime', current_time)
            result = await collection.update_one(
                {'link': item['link']},
                {'$set': item}
            )
            if result.modified_count > 0:
                updated_count += 1
        else:
            # 如果不存在，插入新数据
            item['key'] = str(uuid.uuid4())
            result = await collection.insert_one(item)
            saved_count += 1

    logger.info(f"RSS 解析完成: 新增 {saved_count} 条, 更新 {updated_count} 条")
    return {
        "success": True,
        "source": source_name,
        "saved_count": saved_count,
        "updated_count": updated_count
    }

