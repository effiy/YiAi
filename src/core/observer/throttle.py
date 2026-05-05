"""固定窗口请求限流中间件"""
import time
import logging
from typing import Dict, List, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from core.error_codes import ErrorCode

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

            current = len(active)
            remaining = max(0, self.max_requests - current - 1)

            if current >= self.max_requests:
                retry_after = int(active[0] - cutoff)
                reset_at = int(active[0] + self.window_seconds)
                logger.warning(
                    f"Throttle: {client_ip} exceeded limit "
                    f"{current}/{self.max_requests}/{self.window_seconds}s, "
                    f"retry_after={retry_after}s"
                )
                return JSONResponse(
                    status_code=ErrorCode.RATE_LIMITED.http,
                    content={
                        "code": ErrorCode.RATE_LIMITED.business,
                        "message": ErrorCode.RATE_LIMITED.message,
                        "data": {
                            "limit": self.max_requests,
                            "current": current,
                            "remaining": 0,
                            "reset_at": reset_at,
                        },
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(self.max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_at),
                    },
                )

            active.append(now)
            self._requests[client_ip] = active

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self.max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(active[0] + self.window_seconds))
            return response
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
