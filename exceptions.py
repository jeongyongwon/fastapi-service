"""
커스텀 예외 클래스 및 글로벌 예외 핸들러
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


class BaseAPIException(Exception):
    """기본 API 예외 클래스"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class NotFoundException(BaseAPIException):
    """리소스를 찾을 수 없음"""

    def __init__(self, message: str = "리소스를 찾을 수 없습니다"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
        )


class UnauthorizedException(BaseAPIException):
    """인증 실패"""

    def __init__(self, message: str = "인증이 필요합니다"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
        )


class ForbiddenException(BaseAPIException):
    """권한 없음"""

    def __init__(self, message: str = "접근 권한이 없습니다"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
        )


class BadRequestException(BaseAPIException):
    """잘못된 요청"""

    def __init__(self, message: str = "잘못된 요청입니다"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BAD_REQUEST",
        )


class ConflictException(BaseAPIException):
    """리소스 충돌"""

    def __init__(self, message: str = "리소스 충돌이 발생했습니다"):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
        )


class DatabaseException(BaseAPIException):
    """데이터베이스 오류"""

    def __init__(self, message: str = "데이터베이스 오류가 발생했습니다"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
        )


class ExternalServiceException(BaseAPIException):
    """외부 서비스 오류"""

    def __init__(self, message: str = "외부 서비스 오류가 발생했습니다"):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="EXTERNAL_SERVICE_ERROR",
        )


# 글로벌 예외 핸들러
async def base_exception_handler(request: Request, exc: BaseAPIException):
    """커스텀 예외 핸들러"""
    logger.error(
        f"API Error: {exc.error_code} - {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "path": str(request.url.path),
            }
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """데이터 검증 예외 핸들러"""
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(
        f"Validation Error: {errors}",
        extra={"path": request.url.path, "method": request.method},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "입력 데이터 검증에 실패했습니다",
                "details": errors,
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""
    logger.exception(
        f"Unexpected error: {str(exc)}",
        extra={"path": request.url.path, "method": request.method},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "서버 내부 오류가 발생했습니다",
            }
        },
    )
