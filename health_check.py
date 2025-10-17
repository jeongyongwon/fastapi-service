"""
Health check utilities for monitoring service status
"""
import time
from typing import Dict, Any
from logger_config import get_logger

logger = get_logger(__name__)


class HealthChecker:
    """Utility class for performing health checks on various components"""

    def __init__(self):
        self.start_time = time.time()

    def get_uptime(self) -> float:
        """Get service uptime in seconds"""
        return time.time() - self.start_time

    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            # Simulate DB health check
            check_start = time.time()
            time.sleep(0.01)  # Simulate ping
            latency_ms = (time.time() - check_start) * 1000

            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "connection_pool": {
                    "active": 2,
                    "idle": 8,
                    "max": 10
                }
            }
        except Exception as exc:
            logger.error(
                "health_check_failed",
                message="Database health check failed",
                error={"type": type(exc).__name__, "message": str(exc)},
                exc_info=True
            )
            return {
                "status": "unhealthy",
                "error": str(exc)
            }

    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            # Simulate Redis health check
            check_start = time.time()
            time.sleep(0.005)  # Simulate ping
            latency_ms = (time.time() - check_start) * 1000

            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "memory_used_mb": 45.2,
                "memory_peak_mb": 52.1
            }
        except Exception as exc:
            logger.error(
                "health_check_failed",
                message="Redis health check failed",
                error={"type": type(exc).__name__, "message": str(exc)},
                exc_info=True
            )
            return {
                "status": "unhealthy",
                "error": str(exc)
            }

    async def get_full_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        db_health = await self.check_database()
        redis_health = await self.check_redis()

        overall_healthy = (
            db_health.get("status") == "healthy" and
            redis_health.get("status") == "healthy"
        )

        return {
            "status": "healthy" if overall_healthy else "degraded",
            "uptime_seconds": round(self.get_uptime(), 2),
            "timestamp": time.time(),
            "service_name": "fastapi-service",
            "components": {
                "database": db_health,
                "redis": redis_health
            }
        }

    async def check_external_api(self) -> Dict[str, Any]:
        """외부 API 연결 상태 확인"""
        try:
            check_start = time.time()
            time.sleep(0.02)  # 외부 API 호출 시뮬레이션
            latency_ms = (time.time() - check_start) * 1000

            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "endpoint": "https://api.example.com"
            }
        except Exception as exc:
            logger.error(
                "external_api_check_failed",
                message="External API health check failed",
                error={"type": type(exc).__name__, "message": str(exc)},
                exc_info=True
            )
            return {
                "status": "unhealthy",
                "error": str(exc)
            }
