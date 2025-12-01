import logging
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import feedparser
import aiohttp
from datetime import datetime
import uuid
import asyncio
import os
from Resp import RespOk
from database import db

# 配置日志
logger = logging.getLogger(__name__)

# 定时任务相关配置
_rss_scheduler_task: Optional[asyncio.Task] = None
_rss_scheduler_running = False
_rss_scheduler_interval = int(os.getenv("RSS_SCHEDULER_INTERVAL", "3600"))  # 默认1小时（秒）

router = APIRouter(
    prefix="/rss",
    tags=["rss"],
    responses={404: {"description": "Not found"}},
)

class ParseRssRequest(BaseModel):
    url: str
    name: Optional[str] = None

class ParseAllRssRequest(BaseModel):
    force: Optional[bool] = False

class SchedulerConfigRequest(BaseModel):
    interval: Optional[int] = None  # 定时器间隔（秒）
    enabled: Optional[bool] = None  # 是否启用定时器

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

async def get_enabled_rss_sources() -> List[Dict[str, Any]]:
    """获取所有启用的 RSS 源"""
    try:
        await db.initialize()
        collection = db.mongodb.db['seeds']
        
        # 查询所有启用的 RSS 源（enabled 不为 false 的）
        filter_dict = {
            '$or': [
                {'enabled': {'$ne': False}},
                {'enabled': {'$exists': False}}
            ],
            'url': {'$exists': True, '$ne': ''}
        }
        
        cursor = collection.find(filter_dict, {'_id': 0})
        sources = [doc async for doc in cursor]
        
        logger.info(f"找到 {len(sources)} 个启用的 RSS 源")
        return sources
    except Exception as e:
        logger.error(f"获取 RSS 源列表失败: {str(e)}", exc_info=True)
        return []

async def parse_rss_source_safe(url: str, name: Optional[str] = None) -> Dict[str, Any]:
    """安全地解析单个 RSS 源（不抛出异常）"""
    try:
        feed = await fetch_rss_feed(url)
        source_name = name or feed.feed.get('title', '未知源')
        tags = [source_name] if source_name else []
        
        items_to_save = []
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        for entry in feed.entries:
            item_link = entry.get('link', '')
            if not item_link:
                continue
                
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
            
            if entry.get('author'):
                item_data['author'] = entry.get('author')
            
            if entry.get('content'):
                content_list = entry.get('content', [])
                if content_list and len(content_list) > 0:
                    item_data['content'] = content_list[0].get('value', '')
            
            items_to_save.append(item_data)
        
        collection = db.mongodb.db['rss']
        saved_count = 0
        updated_count = 0
        
        for item in items_to_save:
            existing_item = await collection.find_one({'link': item['link']})
            
            if existing_item:
                item['key'] = existing_item.get('key', str(uuid.uuid4()))
                item['createdTime'] = existing_item.get('createdTime', current_time)
                result = await collection.update_one(
                    {'link': item['link']},
                    {'$set': item}
                )
                if result.modified_count > 0:
                    updated_count += 1
            else:
                item['key'] = str(uuid.uuid4())
                await collection.insert_one(item)
                saved_count += 1
        
        return {
            'url': url,
            'source_name': source_name,
            'success': True,
            'total_items': len(items_to_save),
            'saved_count': saved_count,
            'updated_count': updated_count
        }
    except Exception as e:
        logger.error(f"解析 RSS 源 {url} 失败: {str(e)}")
        return {
            'url': url,
            'source_name': name or url,
            'success': False,
            'error': str(e)
        }

async def parse_all_enabled_rss_sources() -> Dict[str, Any]:
    """解析所有启用的 RSS 源"""
    try:
        await db.initialize()
        sources = await get_enabled_rss_sources()
        
        if not sources:
            return {
                'total_sources': 0,
                'success_count': 0,
                'failed_count': 0,
                'results': []
            }
        
        results = []
        success_count = 0
        failed_count = 0
        
        logger.info(f"开始批量解析 {len(sources)} 个 RSS 源")
        
        # 并发解析所有源（限制并发数避免过载）
        semaphore = asyncio.Semaphore(5)  # 最多5个并发
        
        async def parse_with_semaphore(source):
            async with semaphore:
                return await parse_rss_source_safe(
                    source.get('url', ''),
                    source.get('name')
                )
        
        tasks = [parse_with_semaphore(source) for source in sources]
        results = await asyncio.gather(*tasks)
        
        for result in results:
            if result.get('success'):
                success_count += 1
            else:
                failed_count += 1
        
        logger.info(f"批量解析完成: 成功 {success_count} 个，失败 {failed_count} 个")
        
        return {
            'total_sources': len(sources),
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results
        }
    except Exception as e:
        logger.error(f"批量解析 RSS 源失败: {str(e)}", exc_info=True)
        return {
            'total_sources': 0,
            'success_count': 0,
            'failed_count': 0,
            'error': str(e),
            'results': []
        }

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

@router.post("/parse-all")
async def parse_all_rss(request: ParseAllRssRequest = Body(...)):
    """解析所有启用的 RSS 源"""
    try:
        await db.initialize()
        result = await parse_all_enabled_rss_sources()
        
        return RespOk(
            data=result,
            msg=f"批量解析完成: 成功 {result.get('success_count', 0)} 个，失败 {result.get('failed_count', 0)} 个"
        )
    except Exception as e:
        logger.error(f"批量解析 RSS 源失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量解析 RSS 源失败: {str(e)}")

async def rss_scheduler_loop():
    """RSS 定时解析任务循环"""
    global _rss_scheduler_running, _rss_scheduler_interval
    
    logger.info(f"RSS 定时解析任务已启动，间隔: {_rss_scheduler_interval} 秒")
    
    while _rss_scheduler_running:
        try:
            await asyncio.sleep(_rss_scheduler_interval)
            
            if not _rss_scheduler_running:
                break
            
            logger.info("开始执行定时 RSS 解析任务")
            result = await parse_all_enabled_rss_sources()
            logger.info(f"定时 RSS 解析任务完成: 成功 {result.get('success_count', 0)} 个，失败 {result.get('failed_count', 0)} 个")
        except asyncio.CancelledError:
            logger.info("RSS 定时解析任务已取消")
            break
        except Exception as e:
            logger.error(f"RSS 定时解析任务执行失败: {str(e)}", exc_info=True)
            # 即使出错也继续运行，等待下次执行

def start_rss_scheduler():
    """启动 RSS 定时解析任务"""
    global _rss_scheduler_task, _rss_scheduler_running
    
    if _rss_scheduler_task and not _rss_scheduler_task.done():
        logger.warning("RSS 定时解析任务已在运行")
        return
    
    _rss_scheduler_running = True
    _rss_scheduler_task = asyncio.create_task(rss_scheduler_loop())
    logger.info("RSS 定时解析任务已启动")

def stop_rss_scheduler():
    """停止 RSS 定时解析任务"""
    global _rss_scheduler_task, _rss_scheduler_running
    
    _rss_scheduler_running = False
    
    if _rss_scheduler_task and not _rss_scheduler_task.done():
        _rss_scheduler_task.cancel()
        logger.info("RSS 定时解析任务已停止")

def set_scheduler_interval(interval: int):
    """设置定时器间隔（秒）"""
    global _rss_scheduler_interval
    
    if interval < 60:
        raise ValueError("定时器间隔不能小于 60 秒")
    
    _rss_scheduler_interval = interval
    logger.info(f"RSS 定时器间隔已设置为: {interval} 秒")
    
    # 如果任务正在运行，需要重启以应用新间隔
    if _rss_scheduler_running:
        stop_rss_scheduler()
        start_rss_scheduler()

@router.get("/scheduler/status")
async def get_scheduler_status():
    """获取定时器状态"""
    global _rss_scheduler_running, _rss_scheduler_interval, _rss_scheduler_task
    
    return RespOk(data={
        'enabled': _rss_scheduler_running,
        'interval': _rss_scheduler_interval,
        'running': _rss_scheduler_task is not None and not _rss_scheduler_task.done()
    })

@router.post("/scheduler/config")
async def config_scheduler(request: SchedulerConfigRequest = Body(...)):
    """配置定时器"""
    try:
        global _rss_scheduler_running
        
        if request.interval is not None:
            set_scheduler_interval(request.interval)
        
        if request.enabled is not None:
            if request.enabled:
                if not _rss_scheduler_running:
                    start_rss_scheduler()
            else:
                if _rss_scheduler_running:
                    stop_rss_scheduler()
        
        return RespOk(
            data={
                'enabled': _rss_scheduler_running,
                'interval': _rss_scheduler_interval
            },
            msg="定时器配置已更新"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"配置定时器失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"配置定时器失败: {str(e)}")

@router.post("/scheduler/start")
async def start_scheduler():
    """启动定时器"""
    try:
        start_rss_scheduler()
        return RespOk(data={'enabled': True}, msg="定时器已启动")
    except Exception as e:
        logger.error(f"启动定时器失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"启动定时器失败: {str(e)}")

@router.post("/scheduler/stop")
async def stop_scheduler():
    """停止定时器"""
    try:
        stop_rss_scheduler()
        return RespOk(data={'enabled': False}, msg="定时器已停止")
    except Exception as e:
        logger.error(f"停止定时器失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"停止定时器失败: {str(e)}")



