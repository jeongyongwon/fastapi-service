"""
Pydantic 스키마 정의
API 요청/응답 데이터 검증 및 직렬화
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class StatusEnum(str, Enum):
    """상태 enum"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class SeverityEnum(str, Enum):
    """심각도 enum"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class UserCreate(BaseModel):
    """사용자 생성 요청 스키마"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

    @validator("password")
    def password_strength(cls, v):
        """비밀번호 강도 검증"""
        if not any(char.isdigit() for char in v):
            raise ValueError("비밀번호는 최소 1개의 숫자를 포함해야 합니다")
        if not any(char.isupper() for char in v):
            raise ValueError("비밀번호는 최소 1개의 대문자를 포함해야 합니다")
        return v


class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """사용자 업데이트 스키마"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class ErrorLogCreate(BaseModel):
    """에러 로그 생성 스키마"""
    service_name: str
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    user_id: Optional[int] = None
    severity: SeverityEnum = SeverityEnum.ERROR


class ErrorLogResponse(BaseModel):
    """에러 로그 응답 스키마"""
    id: int
    service_name: str
    error_type: str
    error_message: str
    severity: SeverityEnum
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogCreate(BaseModel):
    """감사 로그 생성 스키마"""
    user_id: Optional[int] = None
    action: str
    resource: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogResponse(BaseModel):
    """감사 로그 응답 스키마"""
    id: int
    user_id: Optional[int]
    action: str
    resource: str
    created_at: datetime

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    """헬스체크 응답 스키마"""
    status: str
    timestamp: datetime
    version: str
    database: str
    cache: str


class PaginationParams(BaseModel):
    """페이지네이션 파라미터"""
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """페이지네이션 응답"""
    items: List[BaseModel]
    total: int
    page: int
    page_size: int
    total_pages: int

    @validator("total_pages", pre=True, always=True)
    def calculate_total_pages(cls, v, values):
        """총 페이지 수 계산"""
        total = values.get("total", 0)
        page_size = values.get("page_size", 10)
        return (total + page_size - 1) // page_size if page_size > 0 else 0
