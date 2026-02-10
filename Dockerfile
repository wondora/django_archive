# Python 3.10 slim 버전
FROM python:3.10-slim

WORKDIR /app

# 1. MariaDB 접속을 위한 시스템 패키지 설치 (필수)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 2. 파이썬 패키지 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 3. 소스 복사
COPY . /app/

# 4. 실행 (entrypoint.sh 대신 직접 명령어를 사용해도 됩니다)

# Gunicorn 실행 (옵션 포함)
# --workers 6 : CPU 6코어 활용
# --timeout 300 : 1GB 업로드를 위해 5분 대기
# config.wsgi:application : 프로젝트 폴더명이 config가 맞는지 꼭 확인하세요!
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "6", "--timeout", "300", "archive.wsgi:application"]
