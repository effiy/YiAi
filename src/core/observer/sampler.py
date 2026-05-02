"""尾部采样器 — 固定大小 ring buffer"""
import time
import logging
from collections import deque
from typing import Dict, Optional
from pydantic import BaseModel, Field
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SampleRecord(BaseModel):
    """采样记录"""
    request_id: str = Field(..., description="请求唯一标识")
    path: str = Field(..., description="请求路径")
    method: str = Field(..., description="HTTP 方法")
    status_code: int = Field(..., description="响应状态码")
    duration_ms: float = Field(..., description="耗时毫秒")
    client_ip: str = Field(..., description="客户端 IP")
    timestamp: str = Field(..., description="ISO 时间戳")
    error_message: Optional[str] = Field(None, description="错误信息")


class TailSampler:
    """尾部采样器：仅采样慢请求和错误请求"""

    def __init__(
        self,
        max_size: int = 1000,
        slow_threshold_ms: float = 5000.0,
    ):
        self.max_size = max_size
        self.slow_threshold_ms = slow_threshold_ms
        self._buffer: deque = deque(maxlen=max_size)
        self._starts: Dict[str, float] = {}

    def start(self, request_id: str) -> None:
        self._starts[request_id] = time.perf_counter()

    def finish(
        self,
        request_id: str,
        path: str,
        method: str,
        status_code: int,
        client_ip: str,
        error_message: Optional[str] = None,
    ) -> bool:
        start = self._starts.pop(request_id, None)
        if start is None:
            return False

        duration_ms = (time.perf_counter() - start) * 1000
        if duration_ms < self.slow_threshold_ms and status_code < 500:
            return False

        record = SampleRecord(
            request_id=request_id,
            path=path,
            method=method,
            status_code=status_code,
            duration_ms=round(duration_ms, 3),
            client_ip=client_ip,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            error_message=error_message,
        )
        self._buffer.append(record)
        return True

    def get_records(self) -> list:
        return list(self._buffer)

    @property
    def size(self) -> int:
        return len(self._buffer)


class SamplerMiddleware(BaseHTTPMiddleware):
    """采样中间件：在请求前后调用 TailSampler"""

    def __init__(self, app, sampler: TailSampler):
        super().__init__(app)
        self.sampler = sampler

    async def dispatch(self, request: Request, call_next):
        request_id = str(id(request))
        client_ip = request.client.host if request.client else "unknown"
        self.sampler.start(request_id)
        try:
            response = await call_next(request)
        except Exception as e:
            try:
                self.sampler.finish(
                    request_id, request.url.path, request.method, 500, client_ip, str(e)
                )
            except Exception:
                logger.exception("Sampler finish error")
            raise
        try:
            self.sampler.finish(
                request_id,
                request.url.path,
                request.method,
                response.status_code,
                client_ip,
            )
        except Exception:
            logger.exception("Sampler finish error")
        return response
