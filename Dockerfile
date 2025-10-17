FROM python:3.11-slim

WORKDIR /app

# 로그 디렉토리 생성
RUN mkdir -p /var/log/fastapi-service

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV LOG_PATH=/var/log/fastapi-service

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
