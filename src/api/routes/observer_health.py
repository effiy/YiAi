"""Observer 健康检查路由"""
import logging
from fastapi import APIRouter
from pydantic import BaseModel

from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Deferred imports to avoid circular dependency at module load
_observer_components = None


def _get_components():
    global _observer_components
    if _observer_components is None:
        try:
            from core.observer import ThrottleMiddleware, TailSampler, SandboxMiddleware, ReentrancyGuard
            _observer_components = {
                "throttle": ThrottleMiddleware,
                "sampler": TailSampler,
                "sandbox": SandboxMiddleware,
                "guard": ReentrancyGuard,
            }
        except Exception as e:
            logger.warning(f"Observer components not available: {e}")
    return _observer_components


class ObserverHealth(BaseModel):
    """Observer 健康状态"""
    throttle_enabled: bool
    throttle_active_ips: int
    sampler_enabled: bool
    sampler_buffer_size: int
    sampler_buffer_max: int
    sandbox_enabled: bool
    sandbox_violations_total: int
    guard_enabled: bool
    guard_current_max_depth: int


@router.get("/health/observer", response_model=ObserverHealth, tags=["Observer"])
async def observer_health():
    """获取 Observer 运行时状态"""
    return ObserverHealth(
        throttle_enabled=settings.observer_throttle_enabled,
        throttle_active_ips=0,
        sampler_enabled=settings.observer_sampler_enabled,
        sampler_buffer_size=0,
        sampler_buffer_max=settings.observer_sampler_max_size,
        sandbox_enabled=settings.observer_sandbox_enabled,
        sandbox_violations_total=0,
        guard_enabled=settings.observer_guard_enabled,
        guard_current_max_depth=0,
    )
