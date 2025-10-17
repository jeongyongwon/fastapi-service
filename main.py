"""
FastAPI 예시 애플리케이션
통합 로그 포맷을 사용하여 HTTP 요청, 쿼리, 에러 로그를 생성합니다.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import time
import uuid
from contextlib import asynccontextmanager
import structlog

from logger_config import get_logger
from health_check import HealthChecker


# 로거 생성
logger = get_logger(__name__)

# Health checker instance
health_checker = HealthChecker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행"""
    logger.info("application_started", message="FastAPI application started")
    yield
    logger.info("application_shutdown", message="FastAPI application shutdown")


app = FastAPI(title="FastAPI Logging Example", lifespan=lifespan)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """
    HTTP 요청/응답 로깅 미들웨어
    """
    # 요청별 고유 ID 생성
    request_id = str(uuid.uuid4())
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    span_id = str(uuid.uuid4())

    # 컨텍스트에 trace 정보 바인딩
    structlog.contextvars.bind_contextvars(
        trace_id=trace_id,
        span_id=span_id,
        request_id=request_id
    )

    start_time = time.time()

    # 요청 로그
    logger.info(
        "http_request_started",
        message="HTTP request started",
        http={
            "method": request.method,
            "path": str(request.url.path),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
    )

    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # 응답 로그
        logger.info(
            "http_request_completed",
            message="HTTP request completed",
            http={
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )

        return response
    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000

        # 에러 로그
        logger.error(
            "http_request_failed",
            message=f"HTTP request failed: {str(exc)}",
            http={
                "method": request.method,
                "path": str(request.url.path),
                "duration_ms": round(duration_ms, 2),
                "client_ip": request.client.host if request.client else None,
            },
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            }
        )
        raise
    finally:
        # 컨텍스트 클리어
        structlog.contextvars.clear_contextvars()


@app.get("/")
async def root():
    """루트 엔드포인트"""
    logger.info("root_endpoint_called", message="Root endpoint accessed")
    return {"message": "FastAPI Logging Example", "status": "healthy"}


@app.get("/health")
async def health():
    """Detailed health check endpoint"""
    health_status = await health_checker.get_full_status()

    logger.info(
        "health_check_performed",
        message="Health check performed",
        context={
            "status": health_status["status"],
            "uptime_seconds": health_status["uptime_seconds"]
        }
    )

    return health_status


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """
    사용자 조회 엔드포인트 (DB 쿼리 로그 예시)
    """
    # Validation: user_id must be positive
    if user_id <= 0:
        logger.warning(
            "invalid_user_id",
            message="Invalid user ID provided",
            context={"user_id": user_id}
        )
        raise HTTPException(status_code=400, detail="User ID must be positive")

    # 쿼리 실행 시뮬레이션
    query_start = time.time()

    # 실제로는 DB 쿼리 실행
    # 여기서는 시뮬레이션
    time.sleep(0.045)  # 45ms 쿼리 시간

    query_duration = (time.time() - query_start) * 1000

    # 쿼리 로그
    logger.info(
        "database_query_executed",
        message="Database query executed",
        query={
            "type": "SELECT",
            "statement": "SELECT * FROM users WHERE id = ?",
            "duration_ms": round(query_duration, 2),
            "rows_affected": 1,
            "database": "user_db"
        },
        context={
            "user_id": user_id
        }
    )

    return {
        "user_id": user_id,
        "name": "John Doe",
        "email": "john@example.com"
    }


@app.post("/users")
async def create_user(user_data: dict):
    """
    사용자 생성 엔드포인트 (INSERT 쿼리 로그 예시)
    """
    query_start = time.time()

    # INSERT 시뮬레이션
    time.sleep(0.032)

    query_duration = (time.time() - query_start) * 1000

    # 쿼리 로그
    logger.info(
        "database_query_executed",
        message="Database query executed",
        query={
            "type": "INSERT",
            "statement": "INSERT INTO users (name, email) VALUES (?, ?)",
            "duration_ms": round(query_duration, 2),
            "rows_affected": 1,
            "database": "user_db"
        }
    )

    return {"status": "created", "user_id": 123}


@app.get("/error")
async def trigger_error():
    """
    에러 발생 엔드포인트 (에러 로그 예시)
    """
    try:
        # 의도적으로 에러 발생
        result = perform_division(1, 0)
    except Exception as exc:
        # 에러 로그 (스택 트레이스 및 위치 정보 포함)
        logger.error(
            "operation_failed",
            message="Division by zero error occurred",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "divide",
                "endpoint": "/error"
            },
            exc_info=True  # 스택 트레이스 자동 추가 (location도 자동 추가됨)
        )

        raise HTTPException(status_code=500, detail="Internal server error")


def perform_division(a: int, b: int) -> float:
    """에러 발생 위치를 명확히 하기 위한 헬퍼 함수"""
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b


@app.get("/slow-query")
async def slow_query():
    """
    느린 쿼리 로그 예시 (성능 모니터링)
    """
    query_start = time.time()

    # 느린 쿼리 시뮬레이션 - 성능 개선 적용
    time.sleep(0.8)  # Optimized from 2.5s to 0.8s with index

    query_duration = (time.time() - query_start) * 1000

    # Performance improved but still log for monitoring
    if query_duration > 1000:
        logger.warning(
            "slow_query_detected",
            message="Slow database query detected",
            query={
                "type": "SELECT",
                "statement": "SELECT * FROM large_table WHERE complex_condition = ? -- optimized with index",
                "duration_ms": round(query_duration, 2),
                "rows_affected": 1000,
                "database": "analytics_db"
            },
            context={
                "threshold_ms": 1000,
                "warning": "Query exceeded performance threshold"
            }
        )
    else:
        logger.info(
            "database_query_executed",
            message="Database query executed",
            query={
                "type": "SELECT",
                "statement": "SELECT * FROM large_table WHERE complex_condition = ? -- optimized with index",
                "duration_ms": round(query_duration, 2),
                "rows_affected": 1000,
                "database": "analytics_db"
            }
        )

    return {"status": "completed", "duration_ms": round(query_duration, 2)}


# ============================================================
# 다양한 에러 시나리오 (RAG 테스트용)
# ============================================================

@app.get("/test/null-pointer")
async def test_null_pointer():
    """Null/None Reference Error"""
    try:
        user = None
        user_name = user.name  # AttributeError 발생
        return {"name": user_name}
    except Exception as exc:
        logger.error(
            "null_pointer_exception",
            message="Null pointer exception occurred",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "access_attribute",
                "endpoint": "/test/null-pointer",
                "attempted_access": "user.name"
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Cannot access attribute of None")


@app.get("/test/attribute-error")
async def test_attribute_error():
    """Attribute Error (유사 시나리오 1)"""
    try:
        data = {"key": "value"}
        result = data.nonexistent_attribute  # AttributeError 발생
        return {"result": result}
    except Exception as exc:
        logger.error(
            "attribute_error",
            message="Attribute access error",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "read_attribute",
                "endpoint": "/test/attribute-error",
                "attempted_access": "data.nonexistent_attribute"
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Attribute does not exist")


@app.get("/test/index-out-of-range")
async def test_index_out_of_range():
    """List Index Out of Range"""
    try:
        items = ['a', 'b', 'c']
        item = items[10]  # IndexError 발생
        return {"item": item}
    except IndexError as exc:
        logger.error(
            "index_out_of_range",
            message="List index out of range error",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "list_access",
                "endpoint": "/test/index-out-of-range",
                "list_length": 3,
                "attempted_index": 10
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Index out of range")


@app.get("/test/key-error")
async def test_key_error():
    """Dictionary Key Error (유사 시나리오 2)"""
    try:
        data = {"name": "test", "age": 30}
        value = data["nonexistent_key"]  # KeyError 발생
        return {"value": value}
    except KeyError as exc:
        logger.error(
            "key_error",
            message="Dictionary key not found",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "dict_access",
                "endpoint": "/test/key-error",
                "available_keys": list({"name": "test", "age": 30}.keys()),
                "requested_key": "nonexistent_key"
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Key not found in dictionary")


@app.get("/test/db-connection-timeout")
async def test_db_connection_timeout():
    """Database Connection Timeout"""
    import asyncio
    start_time = time.time()

    try:
        # DB 연결 타임아웃 시뮬레이션
        await asyncio.sleep(0.1)
        raise TimeoutError("Connection timeout: Unable to connect to database after 5000ms")
    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000

        logger.error(
            "db_connection_timeout",
            message="Database connection timeout",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "db_connect",
                "endpoint": "/test/db-connection-timeout",
                "database": "postgresql",
                "host": "localhost",
                "port": 5432,
                "timeout_ms": 5000,
                "duration_ms": round(duration_ms, 2)
            },
            exc_info=True
        )
        raise HTTPException(status_code=503, detail="Database connection timeout")


@app.get("/test/db-connection-refused")
async def test_db_connection_refused():
    """Database Connection Refused (유사 시나리오 3)"""
    try:
        raise ConnectionRefusedError("Connection refused: ECONNREFUSED 127.0.0.1:5432")
    except Exception as exc:
        logger.error(
            "db_connection_refused",
            message="Database connection refused",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "db_connect",
                "endpoint": "/test/db-connection-refused",
                "database": "postgresql",
                "host": "127.0.0.1",
                "port": 5432,
                "error_code": "ECONNREFUSED"
            },
            exc_info=True
        )
        raise HTTPException(status_code=503, detail="Database connection refused")


@app.get("/test/redis-connection-error")
async def test_redis_connection_error():
    """Redis Connection Error"""
    try:
        raise ConnectionError("Redis connection failed: connect ECONNREFUSED 127.0.0.1:6379")
    except Exception as exc:
        logger.error(
            "redis_connection_error",
            message="Redis connection error",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "redis_connect",
                "endpoint": "/test/redis-connection-error",
                "redis_host": "127.0.0.1",
                "redis_port": 6379,
                "error_code": "ECONNREFUSED"
            },
            exc_info=True
        )
        raise HTTPException(status_code=503, detail="Redis connection failed")


@app.get("/test/redis-timeout")
async def test_redis_timeout():
    """Redis Operation Timeout (유사 시나리오 4)"""
    try:
        raise TimeoutError("Redis operation timeout: GET operation exceeded 2000ms")
    except Exception as exc:
        logger.error(
            "redis_timeout",
            message="Redis operation timeout",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "redis_get",
                "endpoint": "/test/redis-timeout",
                "redis_host": "127.0.0.1",
                "redis_port": 6379,
                "timeout_ms": 2000,
                "redis_operation": "GET"
            },
            exc_info=True
        )
        raise HTTPException(status_code=504, detail="Redis operation timeout")


@app.get("/test/json-decode-error")
async def test_json_decode_error():
    """JSON Decode Error"""
    import json
    try:
        invalid_json = '{name: "test", invalid}'
        parsed = json.loads(invalid_json)
        return parsed
    except json.JSONDecodeError as exc:
        logger.error(
            "json_decode_error",
            message="JSON decode error",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "parse_json",
                "endpoint": "/test/json-decode-error",
                "input": invalid_json,
                "line": exc.lineno,
                "column": exc.colno
            },
            exc_info=True
        )
        raise HTTPException(status_code=400, detail="Invalid JSON format")


@app.get("/test/type-error")
async def test_type_error():
    """Type Conversion Error (유사 시나리오 5)"""
    try:
        value = "not a number"
        number = int(value)  # ValueError 발생
        return {"number": number}
    except ValueError as exc:
        logger.error(
            "type_conversion_error",
            message="Type conversion error",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "type_convert",
                "endpoint": "/test/type-error",
                "from_type": "string",
                "to_type": "int",
                "value": "not a number"
            },
            exc_info=True
        )
        raise HTTPException(status_code=400, detail="Type conversion failed")


@app.get("/test/file-not-found")
async def test_file_not_found():
    """File Not Found Error"""
    try:
        with open('/nonexistent/path/config.json', 'r') as f:
            content = f.read()
        return {"content": content}
    except FileNotFoundError as exc:
        logger.error(
            "file_not_found",
            message="File not found error",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "read_file",
                "endpoint": "/test/file-not-found",
                "file_path": "/nonexistent/path/config.json",
                "error_code": exc.errno
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Configuration file not found")


@app.get("/test/permission-error")
async def test_permission_error():
    """Permission Denied Error (유사 시나리오 6)"""
    try:
        raise PermissionError("[Errno 13] Permission denied: '/etc/protected/config.json'")
    except PermissionError as exc:
        logger.error(
            "permission_denied",
            message="Permission denied error",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "write_file",
                "endpoint": "/test/permission-error",
                "file_path": "/etc/protected/config.json",
                "error_code": 13
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Permission denied")


@app.get("/test/memory-error")
async def test_memory_error():
    """Memory Error Simulation"""
    try:
        # 메모리 할당 시뮬레이션 (실제로는 메모리 에러를 발생시키지 않음)
        large_list = [0] * 10000000
        logger.warning(
            "high_memory_usage",
            message="High memory usage detected",
            context={
                "operation": "memory_allocation",
                "endpoint": "/test/memory-error",
                "allocated_items": len(large_list),
                "estimated_memory_mb": len(large_list) * 8 / 1024 / 1024
            }
        )
        return {
            "warning": "Memory allocation simulation",
            "allocated_items": len(large_list)
        }
    except MemoryError as exc:
        logger.error(
            "memory_error",
            message="Memory allocation failed",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "memory_allocation",
                "endpoint": "/test/memory-error"
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Memory allocation failed")


@app.get("/test/recursion-error")
async def test_recursion_error():
    """Recursion Error / Stack Overflow"""
    try:
        def recursive_function(depth):
            return recursive_function(depth + 1)

        recursive_function(0)
        return {"status": "ok"}
    except RecursionError as exc:
        logger.error(
            "recursion_error",
            message="Maximum recursion depth exceeded",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "recursive_call",
                "endpoint": "/test/recursion-error",
                "recursion_depth": "exceeded"
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Maximum recursion depth exceeded")


@app.get("/test/http-client-error")
async def test_http_client_error():
    """HTTP Client Request Error"""
    try:
        raise Exception("HTTP request failed: connect ETIMEDOUT external-api.com:443")
    except Exception as exc:
        logger.error(
            "http_client_error",
            message="HTTP client request error",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "http_request",
                "endpoint": "/test/http-client-error",
                "target_url": "https://external-api.com/api/data",
                "error_code": "ETIMEDOUT",
                "timeout_ms": 5000
            },
            exc_info=True
        )
        raise HTTPException(status_code=502, detail="External API request failed")


@app.get("/test/circuit-breaker-open")
async def test_circuit_breaker_open():
    """Circuit Breaker Open Error (유사 시나리오 7)"""
    try:
        raise Exception("Circuit breaker is OPEN: too many failures detected for external-api.com")
    except Exception as exc:
        logger.error(
            "circuit_breaker_open",
            message="Circuit breaker open",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "http_request",
                "endpoint": "/test/circuit-breaker-open",
                "target_service": "external-api.com",
                "circuit_state": "OPEN",
                "failure_count": 5,
                "threshold": 5
            },
            exc_info=True
        )
        raise HTTPException(status_code=503, detail="Service temporarily unavailable (circuit breaker open)")


@app.get("/test/rate-limit-exceeded")
async def test_rate_limit_exceeded():
    """Rate Limit Exceeded"""
    try:
        raise Exception("Rate limit exceeded: 429 Too Many Requests")
    except Exception as exc:
        logger.error(
            "rate_limit_exceeded",
            message="Rate limit exceeded",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "api_call",
                "endpoint": "/test/rate-limit-exceeded",
                "rate_limit": 100,
                "window": "1 minute",
                "current_count": 105
            },
            exc_info=True
        )
        raise HTTPException(status_code=429, detail="Too many requests")


@app.get("/test/auth-token-expired")
async def test_auth_token_expired():
    """Authentication Token Expired"""
    try:
        raise Exception("JWT token expired at 2025-10-15T12:00:00Z")
    except Exception as exc:
        logger.error(
            "auth_token_expired",
            message="Authentication token expired",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "authenticate",
                "endpoint": "/test/auth-token-expired",
                "token_type": "JWT",
                "expired_at": "2025-10-15T12:00:00Z"
            },
            exc_info=True
        )
        raise HTTPException(status_code=401, detail="Token expired")


@app.get("/test/import-error")
async def test_import_error():
    """Import/Module Not Found Error"""
    try:
        import nonexistent_module
        return {"status": "ok"}
    except ImportError as exc:
        logger.error(
            "import_error",
            message="Module import failed",
            error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
            context={
                "operation": "import_module",
                "endpoint": "/test/import-error",
                "module_name": "nonexistent_module"
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Module import failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
