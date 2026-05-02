import logging
from typing import Any, Dict, List, Optional, AsyncIterator
from pydantic import ValidationError

from models.schemas import SessionState, AdaptationResult

logger = logging.getLogger(__name__)


class SessionAdapter:
    """遗留 sessions 文档适配器"""

    @staticmethod
    def adapt(document: Dict[str, Any]) -> SessionState:
        """将单个遗留 session 文档转换为结构化 SessionState

        Args:
            document: 来自 sessions 集合的原始文档

        Returns:
            SessionState Pydantic 模型
        """
        mapped = {
            "key": document.get("key", ""),
            "page_content": document.get("pageContent", ""),
            "messages": document.get("messages", []),
            "metadata": {},
            "created_time": document.get("createdTime", ""),
            "updated_time": document.get("updatedTime", ""),
        }

        # 将非标准字段放入 metadata
        known_fields = {"key", "pageContent", "messages", "createdTime", "updatedTime"}
        for k, v in document.items():
            if k not in known_fields:
                mapped["metadata"][k] = v

        try:
            return SessionState.model_validate(mapped)
        except ValidationError as e:
            logger.warning(f"Session adaptation validation error: {e}")
            # 回退到宽松构造
            return SessionState(**mapped)

    @staticmethod
    async def adapt_batch(
        cursor: AsyncIterator[Dict[str, Any]],
        batch_size: int = 100,
    ) -> AdaptationResult:
        """批量适配 session 文档

        Args:
            cursor: MongoDB 查询游标
            batch_size: 每批处理数量（仅用于日志进度）

        Returns:
            AdaptationResult 包含成功数、失败数和错误列表
        """
        success_count = 0
        failure_count = 0
        errors: List[Dict[str, Any]] = []
        processed = 0

        async for doc in cursor:
            try:
                SessionAdapter.adapt(doc)
                success_count += 1
            except Exception as e:
                failure_count += 1
                errors.append({
                    "key": doc.get("key", "unknown"),
                    "error": str(e),
                })
                logger.warning(f"Adaptation failed for {doc.get('key')}: {e}")

            processed += 1
            if processed % batch_size == 0:
                logger.info(f"Adaptation progress: {processed} processed")

        return AdaptationResult(
            success_count=success_count,
            failure_count=failure_count,
            errors=errors,
        )
