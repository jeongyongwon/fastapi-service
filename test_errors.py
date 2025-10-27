"""
테스트용 에러 API 엔드포인트
다양한 종류의 에러를 발생시켜 LLM 분석용 데이터를 생성합니다.
"""

from fastapi import APIRouter, HTTPException, Request
from logger_config import get_logger
import structlog
from typing import Optional
import asyncio
import random

router = APIRouter(prefix="/api/test-errors", tags=["Test Errors"])
logger = get_logger(__name__)


@router.get("/1/database-connection")
async def test_database_connection_error():
    """데이터베이스 연결 에러 시뮬레이션"""
    logger.error(
        "Database connection failed",
        error={
            "type": "DatabaseConnectionError",
            "message": "Could not connect to PostgreSQL database at localhost:5432",
            "details": "Connection refused - server may be down or unreachable"
        },
        context={
            "database": "postgres",
            "host": "localhost",
            "port": 5432,
            "retry_count": 3
        }
    )
    raise HTTPException(status_code=503, detail="Database connection failed")


@router.get("/2/null-pointer")
async def test_null_pointer_error():
    """NoneType 에러 시뮬레이션 - 실제 스택 트레이스 발생"""
    # 실제 에러를 발생시켜 스택 트레이스가 로그에 포함되도록 함
    data = None
    result = data["key"]  # This will raise TypeError with full stack trace
    return {"message": "This line will never be reached"}


@router.get("/3/timeout")
async def test_timeout_error():
    """타임아웃 에러 시뮬레이션"""
    logger.error(
        "Request timeout exceeded",
        error={
            "type": "TimeoutError",
            "message": "External API request timed out after 30 seconds",
            "details": "Third-party payment API did not respond within timeout limit"
        },
        context={
            "api_endpoint": "https://payment-api.example.com/charge",
            "timeout_seconds": 30,
            "retry_attempt": 2
        }
    )
    raise HTTPException(status_code=504, detail="Gateway timeout")


@router.get("/4/authentication")
async def test_authentication_error():
    """인증 에러 시뮬레이션"""
    logger.error(
        "Authentication failed - invalid credentials",
        error={
            "type": "AuthenticationError",
            "message": "JWT token validation failed",
            "details": "Token signature verification failed or token expired"
        },
        context={
            "user_id": "unknown",
            "token_type": "Bearer",
            "ip_address": "192.168.1.100"
        }
    )
    raise HTTPException(status_code=401, detail="Unauthorized - invalid token")


@router.get("/5/permission-denied")
async def test_permission_error():
    """권한 에러 시뮬레이션"""
    logger.error(
        "Permission denied for user action",
        error={
            "type": "PermissionError",
            "message": "User does not have required permissions",
            "details": "Required role: ADMIN, User role: USER"
        },
        context={
            "user_id": "user123",
            "user_role": "USER",
            "required_role": "ADMIN",
            "action": "delete_user"
        }
    )
    raise HTTPException(status_code=403, detail="Forbidden - insufficient permissions")


@router.get("/6/validation")
async def test_validation_error():
    """데이터 검증 에러 시뮬레이션"""
    logger.error(
        "Data validation failed",
        error={
            "type": "ValidationError",
            "message": "Invalid input data format",
            "details": "Email format is invalid and age must be between 0 and 150"
        },
        context={
            "field_errors": {
                "email": "Invalid email format",
                "age": "Must be between 0 and 150",
                "phone": "Required field missing"
            },
            "input_data": {
                "email": "invalid-email",
                "age": -5
            }
        }
    )
    raise HTTPException(status_code=422, detail="Validation error")


@router.get("/7/resource-not-found")
async def test_resource_not_found_error():
    """리소스 없음 에러 시뮬레이션"""
    resource_id = "prod_12345"
    logger.error(
        "Resource not found in database",
        error={
            "type": "ResourceNotFoundError",
            "message": f"Product with ID {resource_id} does not exist",
            "details": "Requested resource could not be found in the database"
        },
        context={
            "resource_type": "Product",
            "resource_id": resource_id,
            "query": f"SELECT * FROM products WHERE id = '{resource_id}'"
        }
    )
    raise HTTPException(status_code=404, detail=f"Product {resource_id} not found")


@router.get("/8/rate-limit")
async def test_rate_limit_error():
    """Rate Limit 에러 시뮬레이션"""
    logger.error(
        "Rate limit exceeded for API endpoint",
        error={
            "type": "RateLimitError",
            "message": "Too many requests from this IP address",
            "details": "Maximum 100 requests per minute exceeded"
        },
        context={
            "ip_address": "192.168.1.100",
            "requests_count": 150,
            "limit": 100,
            "window_minutes": 1,
            "retry_after_seconds": 45
        }
    )
    raise HTTPException(status_code=429, detail="Too many requests - rate limit exceeded")


@router.get("/9/external-api-failure")
async def test_external_api_error():
    """외부 API 호출 실패 시뮬레이션"""
    logger.error(
        "External API call failed",
        error={
            "type": "ExternalAPIError",
            "message": "Third-party weather API returned error",
            "details": "API returned 500 Internal Server Error"
        },
        context={
            "api_name": "WeatherAPI",
            "endpoint": "https://api.weather.com/v1/current",
            "status_code": 500,
            "response_time_ms": 2500,
            "retry_count": 3
        }
    )
    raise HTTPException(status_code=502, detail="Bad gateway - external service unavailable")


@router.get("/10/memory-overflow")
async def test_memory_error():
    """메모리 부족 에러 시뮬레이션"""
    logger.error(
        "Memory allocation failed",
        error={
            "type": "MemoryError",
            "message": "Insufficient memory to complete operation",
            "details": "Failed to allocate 2GB for data processing task"
        },
        context={
            "operation": "large_dataset_processing",
            "requested_memory_mb": 2048,
            "available_memory_mb": 512,
            "dataset_size_records": 10000000
        }
    )
    raise HTTPException(status_code=507, detail="Insufficient storage")


@router.get("/11/deadlock")
async def test_deadlock_error():
    """데드락 에러 시뮬레이션"""
    logger.error(
        "Database deadlock detected",
        error={
            "type": "DeadlockError",
            "message": "Deadlock found when trying to get lock",
            "details": "Transaction was rolled back due to deadlock"
        },
        context={
            "transaction_id": "txn_78901",
            "tables_involved": ["users", "orders"],
            "lock_wait_timeout_seconds": 50,
            "retry_suggested": True
        }
    )
    raise HTTPException(status_code=409, detail="Conflict - deadlock detected")


@router.get("/12/file-not-found")
async def test_file_error():
    """파일 시스템 에러 시뮬레이션"""
    logger.error(
        "File operation failed",
        error={
            "type": "FileNotFoundError",
            "message": "Required configuration file not found",
            "details": "config.yaml file is missing from /etc/app/ directory"
        },
        context={
            "file_path": "/etc/app/config.yaml",
            "operation": "read",
            "working_directory": "/app"
        }
    )
    raise HTTPException(status_code=500, detail="Configuration file missing")


# ===== 스택 트레이스 발생 에러 (13-22번) =====

@router.get("/13/division-by-zero")
async def test_division_by_zero_error():
    """ZeroDivisionError - 실제 스택 트레이스 발생"""
    result = 100 / 0  # ZeroDivisionError
    return {"result": result}


@router.get("/14/index-out-of-range")
async def test_index_error():
    """IndexError - 실제 스택 트레이스 발생"""
    items = [1, 2, 3]
    value = items[10]  # IndexError: list index out of range
    return {"value": value}


@router.get("/15/key-error")
async def test_key_error():
    """KeyError - 실제 스택 트레이스 발생"""
    data = {"name": "John", "age": 30}
    email = data["email"]  # KeyError: 'email'
    return {"email": email}


@router.get("/16/attribute-error")
async def test_attribute_error():
    """AttributeError - 실제 스택 트레이스 발생"""
    obj = None
    result = obj.some_method()  # AttributeError: 'NoneType' object has no attribute 'some_method'
    return {"result": result}


@router.get("/17/type-error")
async def test_type_error():
    """TypeError - 실제 스택 트레이스 발생"""
    result = "string" + 123  # TypeError: can only concatenate str (not "int") to str
    return {"result": result}


@router.get("/18/value-error")
async def test_value_error():
    """ValueError - 실제 스택 트레이스 발생"""
    number = int("not_a_number")  # ValueError: invalid literal for int()
    return {"number": number}


@router.get("/19/import-error")
async def test_import_error():
    """ImportError - 실제 스택 트레이스 발생"""
    import nonexistent_module  # ModuleNotFoundError
    return {"module": "imported"}


@router.get("/20/recursion-error")
async def test_recursion_error():
    """RecursionError - 실제 스택 트레이스 발생"""
    def infinite_recursion():
        return infinite_recursion()

    result = infinite_recursion()  # RecursionError: maximum recursion depth exceeded
    return {"result": result}


@router.get("/21/json-decode-error")
async def test_json_decode_error():
    """JSONDecodeError - 실제 스택 트레이스 발생"""
    import json
    data = json.loads("{invalid json}")  # JSONDecodeError
    return {"data": data}


@router.get("/22/assertion-error")
async def test_assertion_error():
    """AssertionError - 실제 스택 트레이스 발생"""
    user_age = -5
    assert user_age > 0, "Age must be positive"  # AssertionError
    return {"age": user_age}
