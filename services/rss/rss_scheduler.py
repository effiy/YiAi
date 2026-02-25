"""RSS 定时解析与入库
- 按配置周期拉取 RSS，解析条目并写入数据库
- 提供启动/停止与动态配置能力
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from core.database import db
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from core.settings import settings
from services.rss.feed_service import process_feed_from_url

logger = logging.getLogger(__name__)


class RSSSchedulerManager:
    """RSS 调度器管理器，封装调度器状态和配置"""

    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._running = False
        self._config: Dict[str, Any] = {
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

    @property
    def is_running(self) -> bool:
        """调度器是否正在运行"""
        return self._running

    @property
    def config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self._config.copy()

    def get_scheduler(self) -> AsyncIOScheduler:
        """获取或创建调度器实例"""
        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler()
        return self._scheduler

    async def parse_all_sources(self) -> Dict[str, Any]:
        """解析所有启用的 RSS 源"""
        try:
            await db.initialize()
            sources = await self._get_enabled_sources()

            if not sources:
                return {
                    'total_sources': 0,
                    'success_count': 0,
                    'failed_count': 0,
                    'results': []
                }

            logger.info(f"开始批量解析 {len(sources)} 个 RSS 源")

            sem = asyncio.Semaphore(3)

            async def worker(source):
                url = source.get('url')
                name = source.get('name')
                if not url:
                    return None

                async with sem:
                    return await process_feed_from_url(url, name)

            tasks = [worker(source) for source in sources]
            raw_results = await asyncio.gather(*tasks)
            results = [r for r in raw_results if r is not None]

            success_count = sum(1 for r in results if r.get('success'))
            failed_count = len(results) - success_count

            return {
                'total_sources': len(sources),
                'success_count': success_count,
                'failed_count': failed_count,
                'results': results
            }
        except Exception as e:
            logger.error(f"批量解析失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"批量解析失败: {str(e)}")

    async def _get_enabled_sources(self) -> List[Dict[str, Any]]:
        """获取所有启用的 RSS 源配置"""
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

    async def _scheduler_job(self):
        """RSS 定时任务执行体"""
        try:
            logger.info("开始执行定时 RSS 解析任务")
            result = await self.parse_all_sources()
            logger.info(f"定时 RSS 解析任务完成: 成功 {result.get('success_count', 0)} 个，失败 {result.get('failed_count', 0)} 个")
        except Exception as e:
            logger.error(f"RSS 定时解析任务执行失败: {str(e)}", exc_info=True)

    def start(self):
        """启动 RSS 定时解析任务"""
        if self._running:
            logger.warning("RSS 定时解析任务已在运行")
            return

        scheduler = self.get_scheduler()
        scheduler.remove_all_jobs()

        config = self._config
        if config['type'] == 'cron' and config.get('cron'):
            cron_config = config['cron']
            trigger_kwargs = {
                k: v for k, v in cron_config.items()
                if v is not None and k in ['second', 'minute', 'hour', 'day', 'month', 'day_of_week']
            }
            trigger = CronTrigger(**trigger_kwargs)
            logger.info(f"RSS 定时解析任务已启动（Cron模式）: {trigger_kwargs}")
        else:
            interval = config.get('interval', 3600)
            trigger = IntervalTrigger(seconds=interval)
            logger.info(f"RSS 定时解析任务已启动（间隔模式）: {interval} 秒")

        scheduler.add_job(
            self._scheduler_job,
            trigger=trigger,
            id='rss_parse_job',
            replace_existing=True
        )

        if not scheduler.running:
            scheduler.start()

        self._running = True
        logger.info("RSS 定时解析任务已启动")

    def stop(self):
        """停止 RSS 定时解析任务"""
        scheduler = self.get_scheduler()
        if scheduler.running:
            scheduler.shutdown(wait=False)
            self._scheduler = None

        self._running = False
        logger.info("RSS 定时解析任务已停止")

    def set_config(self, config: Dict[str, Any]):
        """设置 RSS 定时器配置"""
        if config.get('type') == 'interval':
            interval = config.get('interval')
            if interval is None:
                interval = self._config.get('interval', 3600)

            if interval < 60:
                raise ValueError("定时器间隔不能小于 60 秒")

            self._config['type'] = 'interval'
            self._config['interval'] = interval
            if 'cron' not in self._config:
                self._config['cron'] = {}

            logger.info(f"RSS 定时器配置已设置为间隔模式: {interval} 秒")
        elif config.get('type') == 'cron':
            cron_config = config.get('cron', {})

            # 验证 cron 配置
            validations = [
                ('second', 0, 59),
                ('minute', 0, 59),
                ('hour', 0, 23),
                ('day', 1, 31),
                ('month', 1, 12),
                ('day_of_week', 0, 6)
            ]

            for field, min_val, max_val in validations:
                if cron_config.get(field) is not None and not (min_val <= cron_config[field] <= max_val):
                    raise ValueError(f"{field} 必须在 {min_val}-{max_val} 之间")

            self._config['type'] = 'cron'
            self._config['cron'] = cron_config
            if 'interval' not in self._config:
                self._config['interval'] = 3600

            logger.info(f"RSS 定时器配置已设置为 Cron 模式: {cron_config}")

        if self._running:
            self.stop()
            self.start()

    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态信息"""
        return {
            'enabled': self._running,
            'type': self._config.get('type', 'interval'),
            'interval': self._config.get('interval'),
            'cron': self._config.get('cron', {})
        }


# 全局单例实例
_scheduler_manager = RSSSchedulerManager()


# 向后兼容的模块级函数，委托给单例实例
async def get_enabled_rss_sources() -> List[Dict[str, Any]]:
    """获取所有启用的 RSS 源配置"""
    return await _scheduler_manager._get_enabled_sources()


async def parse_rss_source_safe(url: str, name: Optional[str] = None) -> Dict[str, Any]:
    """安全解析单个 RSS 源（包含错误处理）"""
    return await process_feed_from_url(url, name)


async def parse_all_enabled_rss_sources(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    解析所有启用的 RSS 源

    Example:
        GET /?module_name=services.rss.rss_scheduler&method_name=parse_all_enabled_rss_sources&parameters={}
    """
    return await _scheduler_manager.parse_all_sources()


async def rss_scheduler_job():
    """RSS 定时任务执行体"""
    await _scheduler_manager._scheduler_job()


def get_scheduler():
    """获取或创建全局调度器实例"""
    return _scheduler_manager.get_scheduler()


def start_rss_scheduler(params: Optional[Dict[str, Any]] = None):
    """
    启动 RSS 定时解析任务

    Example:
        GET /?module_name=services.rss.rss_scheduler&method_name=start_rss_scheduler&parameters={}
    """
    _scheduler_manager.start()


def stop_rss_scheduler(params: Optional[Dict[str, Any]] = None):
    """
    停止 RSS 定时解析任务

    Example:
        GET /?module_name=services.rss.rss_scheduler&method_name=stop_rss_scheduler&parameters={}
    """
    _scheduler_manager.stop()


def set_scheduler_config(params: Dict[str, Any]):
    """
    设置 RSS 定时器配置

    Args:
        params: 配置字典
            - type (str): 'interval' 或 'cron'
            - interval (int): 间隔秒数 (type='interval' 时有效)
            - cron (Dict): Cron 配置 (type='cron' 时有效)

    Example:
        GET /?module_name=services.rss.rss_scheduler&method_name=set_scheduler_config&parameters={"config": {"type": "interval", "interval": 7200}}
    """
    config = params.get('config') if isinstance(params, dict) and isinstance(params.get('config'), dict) else params
    _scheduler_manager.set_config(config)


def get_scheduler_status_info(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    获取调度器状态信息

    Example:
        GET /?module_name=services.rss.rss_scheduler&method_name=get_scheduler_status_info&parameters={}
    """
    return _scheduler_manager.get_status()


def init_rss_system():
    """初始化 RSS 系统"""
    if settings.is_rss_scheduler_enabled():
        try:
            _scheduler_manager.start()
            logger.info("RSS 定时任务已启动")
        except Exception as e:
            logger.warning(f"启动 RSS 定时任务失败: {str(e)}")


def shutdown_rss_system():
    """关闭 RSS 系统（停止定时任务）"""
    if settings.is_rss_scheduler_enabled():
        try:
            _scheduler_manager.stop()
            logger.info("RSS 定时任务已停止")
        except Exception as e:
            logger.warning(f"停止 RSS 定时任务失败: {str(e)}")
