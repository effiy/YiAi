"""懒启动管理器 — 按需初始化 Observer 重型组件"""
import asyncio
import logging
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)


class LazyStartManager:
    """线程/协程安全的按需初始化管理器"""

    def __init__(self):
        self._initialized = False
        self._lock = asyncio.Lock()
        self._init_func: Callable[[], Awaitable[None]] | None = None

    def set_init(self, init_func: Callable[[], Awaitable[None]]) -> None:
        self._init_func = init_func

    async def ensure_initialized(self) -> bool:
        if self._initialized:
            return True
        if self._init_func is None:
            return False
        async with self._lock:
            if self._initialized:
                return True
            try:
                await self._init_func()
                self._initialized = True
                logger.info("LazyStartManager: initialization completed")
            except Exception:
                logger.exception("LazyStartManager: initialization failed")
                return False
        return True

    def reset(self) -> None:
        self._initialized = False
