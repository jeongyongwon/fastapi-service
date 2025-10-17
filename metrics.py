"""
애플리케이션 메트릭 수집 및 모니터링
"""
from typing import Dict, Any
from collections import defaultdict
import time


class MetricsCollector:
    """메트릭 수집기"""

    def __init__(self):
        self.request_count = defaultdict(int)
        self.error_count = defaultdict(int)
        self.response_times = defaultdict(list)
        self.start_time = time.time()

    def record_request(self, endpoint: str, method: str, status_code: int, duration_ms: float):
        """요청 메트릭 기록"""
        key = f"{method}:{endpoint}"
        self.request_count[key] += 1

        if status_code >= 400:
            self.error_count[key] += 1

        self.response_times[key].append(duration_ms)

        # 최근 100개만 유지
        if len(self.response_times[key]) > 100:
            self.response_times[key] = self.response_times[key][-100:]

    def get_metrics(self) -> Dict[str, Any]:
        """수집된 메트릭 조회"""
        metrics = {
            "uptime_seconds": round(time.time() - self.start_time, 2),
            "total_requests": sum(self.request_count.values()),
            "total_errors": sum(self.error_count.values()),
            "endpoints": {}
        }

        for key in self.request_count:
            method, endpoint = key.split(":", 1)
            response_times = self.response_times.get(key, [])

            endpoint_metrics = {
                "method": method,
                "total_requests": self.request_count[key],
                "total_errors": self.error_count[key],
                "error_rate": round(
                    (self.error_count[key] / self.request_count[key] * 100)
                    if self.request_count[key] > 0 else 0,
                    2
                )
            }

            if response_times:
                endpoint_metrics["avg_response_time_ms"] = round(
                    sum(response_times) / len(response_times), 2
                )
                endpoint_metrics["max_response_time_ms"] = round(max(response_times), 2)
                endpoint_metrics["min_response_time_ms"] = round(min(response_times), 2)

            metrics["endpoints"][endpoint] = endpoint_metrics

        return metrics

    def reset(self):
        """메트릭 초기화"""
        self.request_count.clear()
        self.error_count.clear()
        self.response_times.clear()
        self.start_time = time.time()


# 전역 메트릭 수집기
metrics_collector = MetricsCollector()
