# [강의] L20 Docker (DC-04)
#   - Python 기본 환경에 앱과 필요한 라이브러리를 넣어 이미지로 만든다.
#   - 팀원이 각자 실행 환경을 설치하면서 생기는 차이를 줄이려는 목적이다.
# 검증 기록: 파일 작성 전 Dockerfile 부재로 빌드 실패, 작성 후 빌드·실행 성공.
# 이는 수동 빌드·실행 검증이며 pytest 기반 RED 기록을 대신하지 않음.
# 이후 실제 분석·결과 화면 점검 기록은 src/oss_check/web/DOCKER_CHECKLIST.md에 정리함.
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
