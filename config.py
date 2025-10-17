"""
애플리케이션 설정 관리
환경 변수 기반 설정
"""
import os
from typing import Optional


class Settings:
    """애플리케이션 설정 클래스"""

    def __init__(self):
        self.app_name: str = os.getenv("APP_NAME", "fastapi-service")
        self.app_version: str = os.getenv("APP_VERSION", "1.0.0")
        self.environment: str = os.getenv("ENVIRONMENT", "production")
        self.debug_mode: bool = os.getenv("DEBUG", "false").lower() == "true"

        # 데이터베이스 설정
        self.db_host: str = os.getenv("DB_HOST", "localhost")
        self.db_port: int = int(os.getenv("DB_PORT", "5432"))
        self.db_name: str = os.getenv("DB_NAME", "app_db")
        self.db_user: str = os.getenv("DB_USER", "postgres")
        self.db_password: Optional[str] = os.getenv("DB_PASSWORD")

        # Redis 설정
        self.redis_host: str = os.getenv("REDIS_HOST", "localhost")
        self.redis_port: int = int(os.getenv("REDIS_PORT", "6379"))

        # 캐시 설정
        self.cache_ttl: int = int(os.getenv("CACHE_TTL", "60"))
        self.cache_max_size: int = int(os.getenv("CACHE_MAX_SIZE", "1000"))

    def get_db_url(self) -> str:
        """데이터베이스 연결 URL 생성"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


# 전역 설정 인스턴스
settings = Settings()
