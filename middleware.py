"""
커스텀 미들웨어 모음
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
from logger_config import get_logger

logger = get_logger(__name__)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """요청 처리 시간 측정 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000

        # 응답 헤더에 처리 시간 추가
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        # 느린 요청 경고
        if process_time > 1000:
            logger.warning(
                "slow_request_detected",
                message="Slow request detected",
                context={
                    "path": str(request.url.path),
                    "method": request.method,
                    "process_time_ms": round(process_time, 2),
                    "threshold_ms": 1000
                }
            )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """보안 헤더 추가 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 보안 헤더 추가
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
