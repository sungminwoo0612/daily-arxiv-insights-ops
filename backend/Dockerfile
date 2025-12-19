# 1. 베이스 이미지 설정
FROM python:3.10-slim

# 2. 작업 
WORKDIR /app

# 3. 필수 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. 의존성 파일 복사 및 설치
COPY ./backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 복사
COPY ./backend/src/ ./src/
COPY ./backend/data/ ./data/

# 6. 환경변수 설정 (기본값)
ENV PYTHONUNBUFFERED=1

# 7. 포트 설정
EXPOSE 8000

# 8. 서버 실행
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
