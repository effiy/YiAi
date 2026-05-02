import asyncio
import logging
import time
from typing import Any, Dict

from services.state.state_service import StateStoreService
from models.schemas import SkillExecutionRecord

logger = logging.getLogger(__name__)


class SkillRecorder:
    """技能执行结果记录器"""

    def __init__(self, state_service: StateStoreService) -> None:
        self._state = state_service

    async def record(
        self,
        skill_name: str,
        status: str,
        duration_ms: float,
        input_summary: str = "",
        output_summary: str = "",
        error_message: str = "",
    ) -> None:
        """异步记录技能执行结果。失败不抛异常。"""
        try:
            record = SkillExecutionRecord(
                skill_name=skill_name,
                status=status,
                duration_ms=duration_ms,
                input_summary=input_summary,
                output_summary=output_summary,
                error_message=error_message,
            )
            await self._state.create(record.model_dump(exclude={"key"}))
        except Exception as e:
            logger.error(f"SkillRecorder failed to record execution: {e}")

    def record_async(
        self,
        skill_name: str,
        status: str,
        duration_ms: float,
        **kwargs: Any,
    ) -> None:
        """Fire-and-forget 入口。在事件循环中创建后台任务。"""
        try:
            asyncio.create_task(
                self.record(skill_name, status, duration_ms, **kwargs)
            )
        except Exception as e:
            logger.error(f"SkillRecorder failed to schedule task: {e}")


# 全局单例（懒加载）
_recorder_instance: SkillRecorder | None = None


def get_recorder() -> SkillRecorder:
    """获取 SkillRecorder 全局单例"""
    global _recorder_instance
    if _recorder_instance is None:
        _recorder_instance = SkillRecorder(StateStoreService())
    return _recorder_instance
