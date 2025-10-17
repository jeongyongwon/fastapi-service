"""
Celery 백그라운드 작업 정의
비동기 작업, 예약 작업, 주기적 작업 관리
"""
from celery import Celery
from celery.schedules import crontab
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Celery 인스턴스 생성
celery_app = Celery(
    "fastapi_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30분
    worker_prefetch_multiplier=4,
)


@celery_app.task(name="tasks.send_email")
def send_email(to: str, subject: str, body: str):
    """이메일 전송 작업"""
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = "noreply@example.com"
        msg["To"] = to

        # SMTP 서버 연결 (실제 환경에서는 설정 파일에서 로드)
        # with smtplib.SMTP("smtp.example.com", 587) as server:
        #     server.starttls()
        #     server.login("username", "password")
        #     server.send_message(msg)

        logger.info(f"이메일 전송 완료: {to}, 제목: {subject}")
        return {"status": "success", "to": to}
    except Exception as e:
        logger.error(f"이메일 전송 실패: {str(e)}")
        raise


@celery_app.task(name="tasks.process_data")
def process_data(data: dict):
    """데이터 처리 작업"""
    try:
        logger.info(f"데이터 처리 시작: {data}")
        # 데이터 처리 로직
        processed = {
            "original": data,
            "processed_at": datetime.now().isoformat(),
            "status": "completed"
        }
        logger.info("데이터 처리 완료")
        return processed
    except Exception as e:
        logger.error(f"데이터 처리 실패: {str(e)}")
        raise


@celery_app.task(name="tasks.cleanup_old_logs")
def cleanup_old_logs():
    """오래된 로그 정리 작업"""
    try:
        logger.info("로그 정리 작업 시작")
        # 실제로는 DB에서 오래된 로그 삭제
        # delete_old_logs(days=30)
        logger.info("로그 정리 작업 완료")
        return {"status": "success", "deleted_count": 0}
    except Exception as e:
        logger.error(f"로그 정리 실패: {str(e)}")
        raise


@celery_app.task(name="tasks.generate_daily_report")
def generate_daily_report():
    """일일 리포트 생성 작업"""
    try:
        logger.info("일일 리포트 생성 시작")
        # 리포트 생성 로직
        report = {
            "date": datetime.now().date().isoformat(),
            "metrics": {
                "total_requests": 0,
                "error_count": 0,
                "avg_response_time": 0
            }
        }
        logger.info("일일 리포트 생성 완료")
        return report
    except Exception as e:
        logger.error(f"리포트 생성 실패: {str(e)}")
        raise


# 주기적 작업 스케줄
celery_app.conf.beat_schedule = {
    "cleanup-logs-daily": {
        "task": "tasks.cleanup_old_logs",
        "schedule": crontab(hour=2, minute=0),  # 매일 새벽 2시
    },
    "generate-report-daily": {
        "task": "tasks.generate_daily_report",
        "schedule": crontab(hour=23, minute=55),  # 매일 밤 11시 55분
    },
}
