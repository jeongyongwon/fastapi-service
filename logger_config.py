"""
FastAPI용 structlog 기반 로거 설정
통합 로그 포맷 명세에 따라 JSON 로그를 생성합니다.
"""

import structlog
import logging
import sys
import traceback
from datetime import datetime, timezone
import socket
import os
from typing import Any
import pytz

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')


def add_common_fields(logger: Any, method_name: str, event_dict: dict) -> dict:
    """
    모든 로그에 공통 필드를 추가하는 프로세서
    """
    # 공통 필드 추가
    event_dict["service"] = os.getenv("SERVICE_NAME", "fastapi-service")
    event_dict["environment"] = os.getenv("ENVIRONMENT", "development")
    event_dict["host"] = socket.gethostname()

    # timestamp를 ISO 8601 KST 형식으로 변환 (한국 시간)
    if "timestamp" not in event_dict:
        kst_time = datetime.now(KST)
        event_dict["timestamp"] = kst_time.isoformat()

    # level을 대문자로 통일
    if "level" in event_dict:
        event_dict["level"] = event_dict["level"].upper()

    return event_dict


def add_trace_context(logger: Any, method_name: str, event_dict: dict) -> dict:
    """
    분산 추적 컨텍스트를 추가하는 프로세서
    실제 환경에서는 OpenTelemetry 등과 연동
    """
    # 컨텍스트에서 trace_id, span_id 추출 (있는 경우)
    if hasattr(structlog.contextvars, "get_contextvars"):
        ctx = structlog.contextvars.get_contextvars()
        if "trace_id" in ctx:
            event_dict["trace_id"] = ctx["trace_id"]
        if "span_id" in ctx:
            event_dict["span_id"] = ctx["span_id"]

    return event_dict


def add_error_location(logger: Any, method_name: str, event_dict: dict) -> dict:
    """
    에러 발생 시 파일 위치 정보 및 스택 트레이스를 추가하는 프로세서
    """
    # exc_info가 있는 경우 (에러 로그)
    exc_info = event_dict.get("exc_info")
    if exc_info:
        # exc_info가 True인 경우 현재 예외 정보 가져오기
        if exc_info is True:
            import sys
            exc_info = sys.exc_info()

        # 튜플인지 확인
        if isinstance(exc_info, tuple) and len(exc_info) == 3:
            exc_type, exc_value, exc_tb = exc_info

            if exc_tb:
                # error 필드 초기화
                if "error" not in event_dict:
                    event_dict["error"] = {}

                # 전체 스택 트레이스를 문자열로 변환
                tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
                full_traceback = "".join(tb_lines)
                event_dict["error"]["stack_trace"] = full_traceback

                # 스택 트레이스에서 프로젝트 파일 찾기 (site-packages 제외)
                tb = exc_tb
                while tb is not None:
                    frame = tb.tb_frame
                    filename = frame.f_code.co_filename

                    # 프로젝트 파일인지 확인 (site-packages, lib 제외)
                    if "site-packages" not in filename and "/lib/" not in filename and "\\lib\\" not in filename:
                        # 프로젝트 루트 기준 상대 경로로 변환
                        if "/app/" in filename:
                            relative_path = filename.split("/app/")[-1]
                        elif "\\app\\" in filename:
                            relative_path = filename.split("\\app\\")[-1]
                        else:
                            relative_path = os.path.basename(filename)

                        event_dict["error"]["location"] = {
                            "file": relative_path,
                            "line": tb.tb_lineno,
                            "function": frame.f_code.co_name
                        }
                        break

                    tb = tb.tb_next

    return event_dict


def setup_logging():
    """
    structlog 설정 초기화
    """
    # 로그 디렉토리 생성
    log_path = os.getenv("LOG_PATH", "/var/log/fastapi-service")
    try:
        os.makedirs(log_path, exist_ok=True)
    except PermissionError:
        # Fallback to current directory if no permission
        log_path = "./logs"
        os.makedirs(log_path, exist_ok=True)

    # 파일 핸들러 추가 with daily rotation support
    from logging.handlers import TimedRotatingFileHandler

    # 날짜별 파일명 생성을 위한 커스텀 네이머
    def namer(default_name):
        # app.log.2025-10-26 -> app-2025-10-26.log 형식으로 변경
        base_filename, ext, date = default_name.rsplit('.', 2)
        return f"{base_filename}-{date}.log"

    file_handler = TimedRotatingFileHandler(
        f"{log_path}/app.log",
        when='midnight',  # 매일 자정에 로테이션
        interval=1,       # 1일 간격
        backupCount=30,   # 30일치 로그 보관
        encoding='utf-8'
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.namer = namer
    file_handler.setLevel(logging.INFO)

    # 기본 logging 설정
    logging.basicConfig(
        format="%(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            file_handler
        ],
        level=logging.INFO,
    )

    # structlog 설정
    structlog.configure(
        processors=[
            # 컨텍스트 변수 병합
            structlog.contextvars.merge_contextvars,
            # 로그 레벨 추가
            structlog.stdlib.add_log_level,
            # 타임스탬프는 add_common_fields에서 KST로 추가하므로 여기서는 제외
            # 공통 필드 추가 (KST timestamp 포함)
            add_common_fields,
            # 분산 추적 컨텍스트 추가
            add_trace_context,
            # 에러 위치 정보 추가
            add_error_location,
            # 예외 정보 포맷팅
            structlog.processors.format_exc_info,
            # JSON 형식으로 렌더링
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None):
    """
    로거 인스턴스를 가져옵니다.

    Args:
        name: 로거 이름 (보통 __name__ 사용)

    Returns:
        structlog 로거 인스턴스
    """
    return structlog.get_logger(name)


# 로거 초기화
setup_logging()
