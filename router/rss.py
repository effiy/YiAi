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
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# 配置日志
logger = logging.getLogger(__name__)

# 定时任务相关配置
_rss_scheduler: Optional[AsyncIOScheduler] = None
_rss_scheduler_running = False
_rss_scheduler_config: Dict[str, Any] = {
    'type': 'interval',  # 'interval' 或 'cron'
    'interval': int(os.getenv("RSS_SCHEDULER_INTERVAL", "3600")),  # 默认1小时（秒）
    'cron': {
        'second': None,  # 0-59 或 None（表示每分钟）
        'minute': None,  # 0-59 或 None（表示每小时）
        'hour': None,  # 0-23 或 None（表示每天）
        'day': None,  # 1-31 或 None（表示每月）
        'month': None,  # 1-12 或 None（表示每年）
        'day_of_week': None  # 0-6 (0=Monday) 或 None
    }
}

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
    # 兼容旧版本的间隔模式
    interval: Optional[int] = None  # 定时器间隔（秒）
    enabled: Optional[bool] = None  # 是否启用定时器
    
    # 新的 cron 风格配置
    type: Optional[str] = None  # 'interval' 或 'cron'
    cron: Optional[Dict[str, Any]] = None  # cron 配置：{second, minute, hour, day, month, day_of_week}

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

async def rss_scheduler_job():
    """RSS 定时解析任务执行函数"""
    try:
        logger.info("开始执行定时 RSS 解析任务")
        result = await parse_all_enabled_rss_sources()
        logger.info(f"定时 RSS 解析任务完成: 成功 {result.get('success_count', 0)} 个，失败 {result.get('failed_count', 0)} 个")
    except Exception as e:
        logger.error(f"RSS 定时解析任务执行失败: {str(e)}", exc_info=True)

def get_scheduler():
    """获取或创建调度器实例"""
    global _rss_scheduler
    if _rss_scheduler is None:
        _rss_scheduler = AsyncIOScheduler()
    return _rss_scheduler

def start_rss_scheduler():
    """启动 RSS 定时解析任务"""
    global _rss_scheduler_running, _rss_scheduler_config
    
    if _rss_scheduler_running:
        logger.warning("RSS 定时解析任务已在运行")
        return
    
    scheduler = get_scheduler()
    
    # 移除旧任务（如果存在）
    scheduler.remove_all_jobs()
    
    # 根据配置类型创建触发器
    config = _rss_scheduler_config
    if config['type'] == 'cron' and config.get('cron'):
        cron_config = config['cron']
        # 构建 cron 触发器参数（只包含非 None 的值）
        trigger_kwargs = {}
        if cron_config.get('second') is not None:
            trigger_kwargs['second'] = cron_config['second']
        if cron_config.get('minute') is not None:
            trigger_kwargs['minute'] = cron_config['minute']
        if cron_config.get('hour') is not None:
            trigger_kwargs['hour'] = cron_config['hour']
        if cron_config.get('day') is not None:
            trigger_kwargs['day'] = cron_config['day']
        if cron_config.get('month') is not None:
            trigger_kwargs['month'] = cron_config['month']
        if cron_config.get('day_of_week') is not None:
            trigger_kwargs['day_of_week'] = cron_config['day_of_week']
        
        trigger = CronTrigger(**trigger_kwargs)
        logger.info(f"RSS 定时解析任务已启动（Cron模式）: {trigger_kwargs}")
    else:
        # 使用间隔模式
        interval = config.get('interval', 3600)
        trigger = IntervalTrigger(seconds=interval)
        logger.info(f"RSS 定时解析任务已启动（间隔模式）: {interval} 秒")
    
    # 添加任务
    scheduler.add_job(
        rss_scheduler_job,
        trigger=trigger,
        id='rss_parse_job',
        replace_existing=True
    )
    
    # 启动调度器
    if not scheduler.running:
        scheduler.start()
    
    _rss_scheduler_running = True
    logger.info("RSS 定时解析任务已启动")

def stop_rss_scheduler():
    """停止 RSS 定时解析任务"""
    global _rss_scheduler_running, _rss_scheduler
    
    _rss_scheduler_running = False
    
    if _rss_scheduler:
        _rss_scheduler.remove_all_jobs()
        if _rss_scheduler.running:
            _rss_scheduler.shutdown(wait=False)
        logger.info("RSS 定时解析任务已停止")

def set_scheduler_config(config: Dict[str, Any]):
    """设置定时器配置"""
    global _rss_scheduler_config
    
    # 验证配置
    if config.get('type') == 'interval':
        interval = config.get('interval')
        if interval is None:
            # 兼容旧版本：如果只传了 interval，使用 interval 模式
            interval = config.get('interval', 3600)
        if interval < 60:
            raise ValueError("定时器间隔不能小于 60 秒")
        _rss_scheduler_config = {
            'type': 'interval',
            'interval': interval,
            'cron': _rss_scheduler_config.get('cron', {})
        }
        logger.info(f"RSS 定时器配置已设置为间隔模式: {interval} 秒")
    elif config.get('type') == 'cron' or config.get('cron'):
        cron_config = config.get('cron', {})
        # 验证 cron 配置
        if cron_config.get('second') is not None and not (0 <= cron_config['second'] <= 59):
            raise ValueError("秒数必须在 0-59 之间")
        if cron_config.get('minute') is not None and not (0 <= cron_config['minute'] <= 59):
            raise ValueError("分钟数必须在 0-59 之间")
        if cron_config.get('hour') is not None and not (0 <= cron_config['hour'] <= 23):
            raise ValueError("小时数必须在 0-23 之间")
        if cron_config.get('day') is not None and not (1 <= cron_config['day'] <= 31):
            raise ValueError("日期必须在 1-31 之间")
        if cron_config.get('month') is not None and not (1 <= cron_config['month'] <= 12):
            raise ValueError("月份必须在 1-12 之间")
        if cron_config.get('day_of_week') is not None and not (0 <= cron_config['day_of_week'] <= 6):
            raise ValueError("星期数必须在 0-6 之间（0=周一）")
        
        _rss_scheduler_config = {
            'type': 'cron',
            'interval': _rss_scheduler_config.get('interval', 3600),
            'cron': cron_config
        }
        logger.info(f"RSS 定时器配置已设置为 Cron 模式: {cron_config}")
    else:
        # 兼容旧版本：如果只传了 interval，使用 interval 模式
        if 'interval' in config:
            interval = config['interval']
            if interval < 60:
                raise ValueError("定时器间隔不能小于 60 秒")
            _rss_scheduler_config = {
                'type': 'interval',
                'interval': interval,
                'cron': _rss_scheduler_config.get('cron', {})
            }
            logger.info(f"RSS 定时器配置已设置为间隔模式: {interval} 秒")
    
    # 如果任务正在运行，需要重启以应用新配置
    if _rss_scheduler_running:
        stop_rss_scheduler()
        start_rss_scheduler()

@router.get("/scheduler/status")
async def get_scheduler_status():
    """获取定时器状态"""
    global _rss_scheduler_running, _rss_scheduler_config, _rss_scheduler
    
    is_running = False
    if _rss_scheduler:
        jobs = _rss_scheduler.get_jobs()
        is_running = len(jobs) > 0 and _rss_scheduler.running
    
    return RespOk(data={
        'enabled': _rss_scheduler_running,
        'running': is_running,
        'type': _rss_scheduler_config.get('type', 'interval'),
        'interval': _rss_scheduler_config.get('interval'),
        'cron': _rss_scheduler_config.get('cron', {})
    })

@router.post("/scheduler/config")
async def config_scheduler(request: SchedulerConfigRequest = Body(...)):
    """配置定时器"""
    try:
        global _rss_scheduler_running, _rss_scheduler_config
        
        # 构建配置对象
        config_update = {}
        
        # 兼容旧版本：如果只传了 interval，使用 interval 模式
        if request.interval is not None:
            config_update['type'] = 'interval'
            config_update['interval'] = request.interval
        
        # 新的配置方式
        if request.type is not None:
            config_update['type'] = request.type
        
        if request.cron is not None:
            config_update['cron'] = request.cron
        
        # 更新配置
        if config_update:
            set_scheduler_config(config_update)
        
        # 控制启用/禁用
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
                'type': _rss_scheduler_config.get('type', 'interval'),
                'interval': _rss_scheduler_config.get('interval'),
                'cron': _rss_scheduler_config.get('cron', {})
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




