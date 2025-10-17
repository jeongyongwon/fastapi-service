# FastAPI 로깅 예시

structlog를 사용한 FastAPI 애플리케이션의 통합 로그 포맷 구현 예시입니다.

## 주요 기능

- **structlog**: Python의 구조화 로깅 라이브러리
- **JSON 로그 출력**: 파싱하기 쉬운 JSON 형식
- **분산 추적 지원**: trace_id, span_id 컨텍스트 전파
- **HTTP 요청 로깅**: 미들웨어를 통한 자동 로깅
- **쿼리 로깅**: DB 쿼리 실행 시간 및 상세 정보
- **에러 로깅**: 스택 트레이스 포함 에러 로그
- **헬스 체크**: 데이터베이스, Redis, 외부 API 상태 모니터링
- **메트릭 수집**: 엔드포인트별 요청 수, 응답 시간, 에러율 추적
- **인메모리 캐싱**: TTL 기반 캐시로 응답 성능 최적화
- **보안 헤더**: XSS, 클릭재킹 방지 등 보안 헤더 자동 추가

## 설치 및 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env

# 개발 서버 실행
python main.py
```

## Docker 실행

```bash
docker build -t fastapi-logging-example .
docker run -p 8000:8000 \
  -e SERVICE_NAME=fastapi-service \
  -e ENVIRONMENT=production \
  fastapi-logging-example
```

## API 엔드포인트

### Core Endpoints
- `GET /` - 헬스 체크
- `GET /health` - 상세 헬스 체크 (데이터베이스, Redis 상태 포함)
- `GET /users/{user_id}` - 사용자 조회 (캐싱 지원, SELECT 쿼리 로그)
- `POST /users` - 사용자 생성 (유효성 검사, INSERT 쿼리 로그)
- `GET /error` - 에러 로그 테스트
- `GET /slow-query` - 느린 쿼리 경고 로그 테스트

### Test Error Endpoints
다양한 에러 시나리오 테스트를 위한 엔드포인트들이 `/test/*` 경로에 제공됩니다.

## 로그 예시

### HTTP 요청 로그
```json
{
  "timestamp": "2025-10-14T12:34:56.789Z",
  "level": "INFO",
  "service": "fastapi-service",
  "environment": "production",
  "host": "server-01",
  "message": "HTTP request completed",
  "trace_id": "uuid-trace-id",
  "span_id": "uuid-span-id",
  "request_id": "uuid-request-id",
  "http": {
    "method": "GET",
    "path": "/users/123",
    "status_code": 200,
    "duration_ms": 52.34,
    "client_ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
  },
  "event": "http_request_completed"
}
```

### 쿼리 로그
```json
{
  "timestamp": "2025-10-14T12:34:56.789Z",
  "level": "INFO",
  "service": "fastapi-service",
  "environment": "production",
  "host": "server-01",
  "message": "Database query executed",
  "trace_id": "uuid-trace-id",
  "span_id": "uuid-span-id",
  "query": {
    "type": "SELECT",
    "statement": "SELECT * FROM users WHERE id = ?",
    "duration_ms": 45.12,
    "rows_affected": 1,
    "database": "user_db"
  },
  "context": {
    "user_id": 123
  },
  "event": "database_query_executed"
}
```

### 에러 로그
```json
{
  "timestamp": "2025-10-14T12:34:56.789Z",
  "level": "ERROR",
  "service": "fastapi-service",
  "environment": "production",
  "host": "server-01",
  "message": "Division by zero error occurred",
  "trace_id": "uuid-trace-id",
  "span_id": "uuid-span-id",
  "error": {
    "type": "ZeroDivisionError",
    "message": "division by zero"
  },
  "exception": "Traceback (most recent call last):\n  File ...",
  "context": {
    "operation": "divide",
    "endpoint": "/error"
  },
  "event": "operation_failed"
}
```

## 로그 파일 위치

로그는 stdout으로 출력되며, Docker 환경에서는 `/var/log/fastapi-service/app.log`로도 저장됩니다.

Promtail이 수집할 수 있도록 로그 파일 경로를 설정하세요.
