"""RSS 定时解析与入库
- 按配置周期拉取 RSS，解析条目并写入数据库
- 提供启动/停止与动态配置能力
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from core.database import db
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from core.config import settings
from services.rss.feed_service import process_feed_from_url

logger = logging.getLogger(__name__)

_rss_scheduler: Optional[AsyncIOScheduler] = None
_rss_scheduler_running = False
_rss_scheduler_config: Dict[str, Any] = {
    'type': 'interval',
    'interval': settings.rss_scheduler_interval,
    'cron': {
        'second': None,
        'minute': None,
        'hour': None,
        'day': None,
        'month': None,
        'day_of_week': None
    }
}

async def get_enabled_rss_sources() -> List[Dict[str, Any]]:
    """
    获取所有启用的 RSS 源配置
    
    Returns:
        List[Dict[str, Any]]: RSS 源配置列表
    """
    try:
        await db.initialize()
        collection = db.db[settings.collection_seeds]

        filter_dict = {
            '$or': [
                {'enabled': {'$ne': False}},
                {'enabled': {'$exists': False}}
            ],
            'url': {'$exists': True, '$ne': ''}
        }

        cursor = collection.find(filter_dict, {'_id': 0})
        sources = [doc async for doc in cursor]
        return sources
    except Exception as e:
        logger.error(f"获取 RSS 源列表失败: {str(e)}", exc_info=True)
        return []

async def parse_rss_source_safe(url: str, name: Optional[str] = None) -> Dict[str, Any]:
    """
    安全解析单个 RSS 源（包含错误处理）
    Delegates to feed_service.process_feed_from_url
    
    Args:
        url: RSS 源地址
        name: 源名称
    """
    return await process_feed_from_url(url, name)

async def parse_all_enabled_rss_sources() -> Dict[str, Any]:
    """
    解析所有启用的 RSS 源
    
    Returns:
        Dict[str, Any]: 批量解析结果
            - total_sources (int): 总源数
            - success_count (int): 成功数
            - failed_count (int): 失败数
            - results (List[Dict]): 详细结果列表
            
    Raises:
        HTTPException: 执行过程中发生严重错误时抛出
        
    Example:
        GET /?module_name=services.rss.rss_scheduler&method_name=parse_all_enabled_rss_sources&parameters={}
    """
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
        
        for source in sources:
            url = source.get('url')
            name = source.get('name')
            if not url:
                continue
                
            result = await parse_rss_source_safe(url, name)
            results.append(result)
            
            if result.get('success'):
                success_count += 1
            else:
                failed_count += 1
                
        return {
            'total_sources': len(sources),
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results
        }
    except Exception as e:
        logger.error(f"批量解析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量解析失败: {str(e)}")

async def rss_scheduler_job():
    """
    RSS 定时任务执行体
    - 调用 parse_all_enabled_rss_sources 执行所有 RSS 解析
    - 记录执行结果
    """
    try:
        logger.info("开始执行定时 RSS 解析任务")
        result = await parse_all_enabled_rss_sources()
        logger.info(f"定时 RSS 解析任务完成: 成功 {result.get('success_count', 0)} 个，失败 {result.get('failed_count', 0)} 个")
    except Exception as e:
        logger.error(f"RSS 定时解析任务执行失败: {str(e)}", exc_info=True)

def get_scheduler():
    """
    获取或创建全局调度器实例
    
    Returns:
        AsyncIOScheduler: 调度器实例
    """
    global _rss_scheduler
    if _rss_scheduler is None:
        _rss_scheduler = AsyncIOScheduler()
    return _rss_scheduler

def start_rss_scheduler():
    """
    启动 RSS 定时解析任务
    
    Example:
        GET /?module_name=services.rss.rss_scheduler&method_name=start_rss_scheduler&parameters={}
    """
    global _rss_scheduler_running, _rss_scheduler_config

    if _rss_scheduler_running:
        logger.warning("RSS 定时解析任务已在运行")
        return

    scheduler = get_scheduler()

    scheduler.remove_all_jobs()

    config = _rss_scheduler_config
    if config['type'] == 'cron' and config.get('cron'):
        cron_config = config['cron']
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
        interval = config.get('interval', 3600)
        trigger = IntervalTrigger(seconds=interval)
        logger.info(f"RSS 定时解析任务已启动（间隔模式）: {interval} 秒")

    scheduler.add_job(
        rss_scheduler_job,
        trigger=trigger,
        id='rss_parse_job',
        replace_existing=True
    )

    if not scheduler.running:
        scheduler.start()

    _rss_scheduler_running = True
    logger.info("RSS 定时解析任务已启动")

def stop_rss_scheduler():
    """
    停止 RSS 定时解析任务
    
    Example:
        GET /?module_name=services.rss.rss_scheduler&method_name=stop_rss_scheduler&parameters={}
    """
    global _rss_scheduler_running
    
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        global _rss_scheduler
        _rss_scheduler = None
        
    _rss_scheduler_running = False
    logger.info("RSS 定时解析任务已停止")

def set_scheduler_config(config: Dict[str, Any]):
    """
    设置 RSS 定时器配置
    
    Args:
        config: 配置字典
            - type (str): 'interval' 或 'cron'
            - interval (int): 间隔秒数 (type='interval' 时有效)
            - cron (Dict): Cron 配置 (type='cron' 时有效)
            
    Raises:
        ValueError: 配置参数无效时抛出

    Example:
        GET /?module_name=services.rss.rss_scheduler&method_name=set_scheduler_config&parameters={"config": {"type": "interval", "interval": 7200}}
    """
    global _rss_scheduler_config

    if config.get('type') == 'interval':
        interval = config.get('interval')
        if interval is None:
            interval = _rss_scheduler_config.get('interval', 3600)
        
        if interval < 60:
            raise ValueError("定时器间隔不能小于 60 秒")
        
        _rss_scheduler_config['type'] = 'interval'
        _rss_scheduler_config['interval'] = interval
        if 'cron' not in _rss_scheduler_config:
            _rss_scheduler_config['cron'] = {}
            
        logger.info(f"RSS 定时器配置已设置为间隔模式: {interval} 秒")
    elif config.get('type') == 'cron':
        cron_config = config.get('cron', {})
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

        _rss_scheduler_config['type'] = 'cron'
        _rss_scheduler_config['cron'] = cron_config
        if 'interval' not in _rss_scheduler_config:
            _rss_scheduler_config['interval'] = 3600

        logger.info(f"RSS 定时器配置已设置为 Cron 模式: {cron_config}")
    else:
        pass

    if _rss_scheduler_running:
        stop_rss_scheduler()
        start_rss_scheduler()

def get_scheduler_status_info() -> Dict[str, Any]:
    """
    获取调度器状态信息
    
    Example:
        GET /?module_name=services.rss.rss_scheduler&method_name=get_scheduler_status_info&parameters={}
    """
    return {
        'enabled': _rss_scheduler_running,
        'type': _rss_scheduler_config.get('type', 'interval'),
        'interval': _rss_scheduler_config.get('interval'),
        'cron': _rss_scheduler_config.get('cron', {})
    }

def init_rss_system():
    """
    初始化 RSS 系统
    - 检查配置是否启用 RSS 调度器
    - 如果启用，启动调度器
    """
    if settings.is_rss_scheduler_enabled():
        try:
            start_rss_scheduler()
            logger.info("RSS 定时任务已启动")
        except Exception as e:
            logger.warning(f"启动 RSS 定时任务失败: {str(e)}")

def shutdown_rss_system():
    """
    关闭 RSS 系统（停止定时任务）
    - 停止正在运行的调度器
    """
    if settings.is_rss_scheduler_enabled():
        try:
            stop_rss_scheduler()
            logger.info("RSS 定时任务已停止")
        except Exception as e:
            logger.warning(f"停止 RSS 定时任务失败: {str(e)}")
