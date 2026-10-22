# [강의] Docker: Python 실행 환경과 앱을 하나의 이미지로 구성함 (DC-04).
# 검증 기록: 파일 작성 전 Dockerfile 부재로 빌드 실패, 작성 후 빌드·실행 성공.
# 이는 수동 빌드·실행 검증이며 pytest 기반 RED 기록을 대신하지 않음.
# 확인 범위: 입력·예시·CSS·입력 접수. 실제 분석과 최종 인수 시나리오는 미완료.
FROM python:3.11-slim

# 바이트코드 파일 생성을 막고 실행 로그를 바로 출력함.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 설치에 필요한 파일만 복사하며 로컬 가상환경과 Git 기록은 복사하지 않음.
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN python -m pip install --no-cache-dir .

# 앱은 관리자 권한 없이 실행함.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "oss_check.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
