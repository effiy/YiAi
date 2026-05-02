"""重入守卫 — 基于 ContextVar 的异步上下文深度计数器"""
import contextvars
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

_reentrancy_depth: contextvars.ContextVar[int] = contextvars.ContextVar(
    "reentrancy_depth", default=0
)


class ReentrancyExceeded(Exception):
    """重入深度超限异常"""
    def __init__(self, depth: int, limit: int):
        self.depth = depth
        self.limit = limit
        super().__init__(f"Reentrancy depth {depth} exceeds limit {limit}")


class ReentrancyGuard:
    """重入守卫：基于 ContextVar 的深度计数器"""

    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth

    def guard(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            depth = _reentrancy_depth.get()
            if depth >= self.max_depth:
                raise ReentrancyExceeded(depth, self.max_depth)
            token = _reentrancy_depth.set(depth + 1)
            try:
                return await func(*args, **kwargs)
            finally:
                _reentrancy_depth.reset(token)
        return wrapper

    def guard_sync(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            depth = _reentrancy_depth.get()
            if depth >= self.max_depth:
                raise ReentrancyExceeded(depth, self.max_depth)
            token = _reentrancy_depth.set(depth + 1)
            try:
                return func(*args, **kwargs)
            finally:
                _reentrancy_depth.reset(token)
        return wrapper

    @property
    def current_max_depth(self) -> int:
        return _reentrancy_depth.get()
