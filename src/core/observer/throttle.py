"""固定窗口请求限流中间件"""
import time
import logging
from typing import Dict, List, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ThrottleMiddleware(BaseHTTPMiddleware):
    """固定窗口请求限流中间件，按客户端 IP 计数"""

    def __init__(
        self,
        app,
        max_requests: int = 100,
        window_seconds: int = 60,
        whitelist: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.whitelist = set(whitelist or [])
        self._requests: Dict[str, List[float]] = {}
        self._last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next):
        try:
            client_ip = request.client.host if request.client else "unknown"

            if client_ip in self.whitelist:
                return await call_next(request)

            now = time.time()
            self._cleanup(now)

            timestamps = self._requests.get(client_ip, [])
            cutoff = now - self.window_seconds
            active = [t for t in timestamps if t > cutoff]

            if len(active) >= self.max_requests:
                logger.warning(f"Throttle: {client_ip} exceeded limit {self.max_requests}/{self.window_seconds}s")
                return Response(
                    content='{"code":1003,"message":"Too Many Requests"}',
                    status_code=429,
                    headers={"Retry-After": str(self.window_seconds)},
                    media_type="application/json",
                )

            active.append(now)
            self._requests[client_ip] = active
        except Exception:
            logger.exception("Throttle middleware error")

        return await call_next(request)

    def _cleanup(self, now: float) -> None:
        if now - self._last_cleanup < self.window_seconds:
            return
        cutoff = now - self.window_seconds
        self._requests = {
            ip: [t for t in ts if t > cutoff]
            for ip, ts in self._requests.items()
            if any(t > cutoff for t in ts)
        }
        self._last_cleanup = now
