import logging
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import feedparser
import aiohttp
from datetime import datetime
import uuid
from Resp import RespOk
from database import db

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/rss",
    tags=["rss"],
    responses={404: {"description": "Not found"}},
)

class ParseRssRequest(BaseModel):
    url: str
    name: Optional[str] = None

async def fetch_rss_feed(url: str) -> feedparser.FeedParserDict:
    """获取并解析 RSS 源"""
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

@router.post("/parse")
async def parse_rss(request: ParseRssRequest):
    """解析 RSS 源并存入 MongoDB"""
    try:
        # 确保数据库已初始化
        await db.initialize()
        
        # 获取并解析 RSS 源
        logger.info(f"开始解析 RSS 源: {request.url}")
        feed = await fetch_rss_feed(request.url)
        
        # 获取源名称（优先使用传入的 name，否则使用 feed 的 title）
        source_name = request.name or feed.feed.get('title', '未知源')
        
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
                'source_url': request.url,
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
        collection = db.mongodb.db['rss']
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
                # 如果不存在，创建新记录（生成 key）
                item['key'] = str(uuid.uuid4())
                await collection.insert_one(item)
                saved_count += 1
        
        logger.info(f"RSS 源解析完成: 新增 {saved_count} 条，更新 {updated_count} 条")
        
        return RespOk(
            data={
                'source_name': source_name,
                'source_url': request.url,
                'total_items': len(items_to_save),
                'saved_count': saved_count,
                'updated_count': updated_count,
                'tags': tags
            },
            msg=f"成功解析 RSS 源，共处理 {len(items_to_save)} 条数据"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解析 RSS 源时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"解析 RSS 源失败: {str(e)}")


